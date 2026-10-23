package consensus

import (
	"bytes"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"encoding/pem"
	"errors"
	"io"
	"log"
	"net"
	"net/http"
	"sync"
	"time"

	"github.com/hashicorp/raft"
)

const MaxFrame = 16 * 1024 * 1024

type Peer struct {
	ID          string `json:"id"`
	Address     string `json:"address"`
	Certificate string `json:"certificate"`
}

type boundedListener struct {
	net.Listener
	slots chan struct{}
}
type boundedConnection struct {
	net.Conn
	release func()
	once    sync.Once
}

func (c *boundedConnection) Close() error { e := c.Conn.Close(); c.once.Do(c.release); return e }
func (l *boundedListener) Accept() (net.Conn, error) {
	for {
		c, e := l.Listener.Accept()
		if e != nil {
			return nil, e
		}
		select {
		case l.slots <- struct{}{}:
			return &boundedConnection{Conn: c, release: func() { <-l.slots }}, nil
		default:
			c.Close()
		}
	}
}
func limitListener(l net.Listener, n int) net.Listener {
	return &boundedListener{l, make(chan struct{}, n)}
}

type Transport struct {
	id, cluster string
	peers       map[string]Peer
	pins        map[string]string
	consumer    chan raft.RPC
	server      *http.Server
	clients     map[string]*http.Client
	mu          sync.RWMutex
	// Test fault injection only; runtime provides no network-fault endpoint.
	blocked     map[string]bool
	delay       time.Duration
	quarantined func() bool
}

// Certificate roots AND exact certificate fingerprints are checked. The header
// identity/address is bound to the TLS peer before entering upstream Raft.
func NewTransport(id, cluster string, peers []Peer, cert tls.Certificate, listener net.Listener, quarantine ...func() bool) (*Transport, error) {
	t := &Transport{id: id, cluster: cluster, peers: map[string]Peer{}, pins: map[string]string{}, consumer: make(chan raft.RPC, 32), blocked: map[string]bool{}, clients: map[string]*http.Client{}}
	t.quarantined = func() bool { return false }
	if len(quarantine) > 0 {
		t.quarantined = quarantine[0]
	}
	roots := x509.NewCertPool()
	for _, p := range peers {
		if !roots.AppendCertsFromPEM([]byte(p.Certificate)) {
			return nil, errors.New("invalid peer certificate")
		}
		pair, err := certificateDER(p.Certificate)
		if err != nil {
			return nil, err
		}
		pin := sum(pair)
		if _, exists := t.pins[pin]; exists {
			return nil, errors.New("peer certificates must be unique")
		}
		t.peers[p.ID] = p
		t.pins[pin] = p.ID
	}
	if len(t.peers) != 3 || t.peers[id].Address != listener.Addr().String() {
		return nil, errors.New("static three-voter binding mismatch")
	}
	if len(cert.Certificate) == 0 || t.pins[sum(cert.Certificate[0])] != id {
		return nil, errors.New("local certificate identity mismatch")
	}
	serverTLS := &tls.Config{MinVersion: tls.VersionTLS13, Certificates: []tls.Certificate{cert}, ClientCAs: roots, ClientAuth: tls.RequireAndVerifyClientCert}
	serverTLS.VerifyConnection = func(s tls.ConnectionState) error {
		if len(s.PeerCertificates) != 1 || t.pins[sum(s.PeerCertificates[0].Raw)] == "" {
			return errors.New("peer denied")
		}
		return nil
	}
	for peerID := range t.peers {
		clientTLS := &tls.Config{MinVersion: tls.VersionTLS13, Certificates: []tls.Certificate{cert}, RootCAs: roots}
		clientTLS.VerifyConnection = func(s tls.ConnectionState) error {
			if len(s.PeerCertificates) != 1 || t.pins[sum(s.PeerCertificates[0].Raw)] != peerID {
				return errors.New("destination identity mismatch")
			}
			return nil
		}
		t.clients[peerID] = &http.Client{Transport: &http.Transport{TLSClientConfig: clientTLS, MaxConnsPerHost: 4, MaxIdleConnsPerHost: 2, IdleConnTimeout: 5 * time.Second}, Timeout: 10 * time.Second}
	}
	t.server = &http.Server{Handler: t, ReadHeaderTimeout: time.Second, ReadTimeout: 15 * time.Second, WriteTimeout: 15 * time.Second, IdleTimeout: 3 * time.Second, MaxHeaderBytes: 4096, ErrorLog: log.New(io.Discard, "", 0)}
	go t.server.Serve(tls.NewListener(limitListener(listener, 32), serverTLS))
	return t, nil
}

func certificateDER(pemText string) ([]byte, error) {
	pool := x509.NewCertPool()
	if !pool.AppendCertsFromPEM([]byte(pemText)) {
		return nil, errors.New("invalid certificate")
	}
	// Parse the exact PEM rather than treating a CA-issued peer certificate as
	// authority for arbitrary additional cluster identities.
	block, rest := pem.Decode([]byte(pemText))
	if block == nil || len(bytes.TrimSpace(rest)) > 0 || block.Type != "CERTIFICATE" {
		return nil, errors.New("invalid certificate")
	}
	return block.Bytes, nil
}

func (t *Transport) Consumer() <-chan raft.RPC                               { return t.consumer }
func (t *Transport) LocalAddr() raft.ServerAddress                           { return raft.ServerAddress(t.peers[t.id].Address) }
func (t *Transport) EncodePeer(_ raft.ServerID, a raft.ServerAddress) []byte { return []byte(a) }
func (t *Transport) DecodePeer(b []byte) raft.ServerAddress                  { return raft.ServerAddress(b) }
func (t *Transport) SetHeartbeatHandler(func(raft.RPC))                      {}
func (t *Transport) AppendEntriesPipeline(raft.ServerID, raft.ServerAddress) (raft.AppendPipeline, error) {
	return nil, raft.ErrPipelineReplicationNotSupported
}
func (t *Transport) Close() error {
	for _, c := range t.clients {
		c.CloseIdleConnections()
	}
	return t.server.Close()
}

type rpcFrame struct {
	Request  json.RawMessage `json:"request"`
	Snapshot []byte          `json:"snapshot,omitempty"`
}

func (t *Transport) call(id raft.ServerID, target raft.ServerAddress, kind string, args, response interface{}, data []byte) error {
	if t.quarantined() {
		return ErrQuarantine
	}
	p, ok := t.peers[string(id)]
	if !ok || p.Address != string(target) {
		return errors.New("unknown peer")
	}
	t.mu.RLock()
	blocked := t.blocked[string(id)]
	delay := t.delay
	t.mu.RUnlock()
	if blocked {
		return errors.New("injected partition")
	}
	if delay > 0 {
		time.Sleep(delay)
	}
	b, e := json.Marshal(args)
	if e != nil {
		return e
	}
	body, e := json.Marshal(rpcFrame{b, data})
	if e != nil {
		return e
	}
	if len(body) > MaxFrame {
		return errors.New("frame limit")
	}
	req, e := http.NewRequest("POST", "https://"+p.Address+"/raft/v1/"+kind, bytes.NewReader(body))
	if e != nil {
		return e
	}
	req.Header.Set("X-ASC-Cluster", t.cluster)
	req.Header.Set("Content-Type", "application/json")
	// Verify the expected destination certificate in addition to ordinary PKI.
	resp, e := t.clients[string(id)].Do(req)
	if e != nil {
		return e
	}
	defer resp.Body.Close()
	if resp.TLS == nil || len(resp.TLS.PeerCertificates) != 1 || t.pins[sum(resp.TLS.PeerCertificates[0].Raw)] != string(id) {
		return errors.New("destination identity mismatch")
	}
	if resp.StatusCode != 200 {
		return errors.New("peer RPC denied")
	}
	raw, e := io.ReadAll(io.LimitReader(resp.Body, MaxFrame+1))
	if e != nil || len(raw) > MaxFrame {
		return errors.New("response limit")
	}
	return json.Unmarshal(raw, response)
}

func (t *Transport) AppendEntries(id raft.ServerID, a raft.ServerAddress, q *raft.AppendEntriesRequest, r *raft.AppendEntriesResponse) error {
	return t.call(id, a, "append", q, r, nil)
}
func (t *Transport) RequestVote(id raft.ServerID, a raft.ServerAddress, q *raft.RequestVoteRequest, r *raft.RequestVoteResponse) error {
	return t.call(id, a, "vote", q, r, nil)
}
func (t *Transport) RequestPreVote(id raft.ServerID, a raft.ServerAddress, q *raft.RequestPreVoteRequest, r *raft.RequestPreVoteResponse) error {
	return t.call(id, a, "prevote", q, r, nil)
}
func (t *Transport) TimeoutNow(id raft.ServerID, a raft.ServerAddress, q *raft.TimeoutNowRequest, r *raft.TimeoutNowResponse) error {
	return t.call(id, a, "timeout", q, r, nil)
}
func (t *Transport) InstallSnapshot(id raft.ServerID, a raft.ServerAddress, q *raft.InstallSnapshotRequest, r *raft.InstallSnapshotResponse, data io.Reader) error {
	b, e := io.ReadAll(io.LimitReader(data, MaxFrame/2+1))
	if e != nil {
		return e
	}
	if int64(len(b)) != q.Size || len(b) > MaxFrame/2 {
		return errors.New("snapshot limit")
	}
	return t.call(id, a, "snapshot", q, r, b)
}

func (t *Transport) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store")
	deny := func(code int) { http.Error(w, "raft_rpc_denied", code) }
	if r.Method != "POST" || r.TLS == nil || len(r.TLS.PeerCertificates) != 1 || r.Header.Get("X-ASC-Cluster") != t.cluster {
		deny(403)
		return
	}
	id := t.pins[sum(r.TLS.PeerCertificates[0].Raw)]
	if t.quarantined() {
		deny(503)
		return
	}
	if id == "" || id == t.id {
		deny(403)
		return
	}
	t.mu.RLock()
	blocked := t.blocked[id]
	t.mu.RUnlock()
	if blocked {
		deny(503)
		return
	}
	var frame rpcFrame
	dec := json.NewDecoder(http.MaxBytesReader(w, r.Body, MaxFrame))
	dec.DisallowUnknownFields()
	if dec.Decode(&frame) != nil || dec.Decode(new(interface{})) != io.EOF {
		deny(400)
		return
	}
	var command interface{ GetRPCHeader() raft.RPCHeader }
	switch r.URL.Path {
	case "/raft/v1/append":
		command = &raft.AppendEntriesRequest{}
	case "/raft/v1/vote":
		command = &raft.RequestVoteRequest{}
	case "/raft/v1/prevote":
		command = &raft.RequestPreVoteRequest{}
	case "/raft/v1/timeout":
		command = &raft.TimeoutNowRequest{}
	case "/raft/v1/snapshot":
		command = &raft.InstallSnapshotRequest{}
	default:
		deny(404)
		return
	}
	dec = json.NewDecoder(bytes.NewReader(frame.Request))
	dec.DisallowUnknownFields()
	if dec.Decode(command) != nil {
		deny(400)
		return
	}
	header := command.GetRPCHeader()
	p := t.peers[id]
	if string(header.ID) != id || string(header.Addr) != p.Address || header.ProtocolVersion != raft.ProtocolVersionMax {
		deny(403)
		return
	}
	if q, ok := command.(*raft.AppendEntriesRequest); ok {
		if len(q.Entries) > 64 || (len(q.Leader) > 0 && string(q.Leader) != p.Address) {
			deny(400)
			return
		}
	}
	if q, ok := command.(*raft.RequestVoteRequest); ok && len(q.Candidate) > 0 && string(q.Candidate) != p.Address {
		deny(403)
		return
	}
	if q, ok := command.(*raft.InstallSnapshotRequest); ok {
		if q.Size != int64(len(frame.Snapshot)) || len(frame.Snapshot) > MaxFrame/2 {
			deny(400)
			return
		}
	} else if len(frame.Snapshot) > 0 {
		deny(400)
		return
	}
	ch := make(chan raft.RPCResponse, 1)
	rpc := raft.RPC{Command: command, RespChan: ch, Reader: bytes.NewReader(frame.Snapshot)}
	select {
	case t.consumer <- rpc:
	case <-r.Context().Done():
		return
	case <-time.After(time.Second):
		deny(503)
		return
	}
	select {
	case resp := <-ch:
		if resp.Error != nil {
			deny(503)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp.Response)
	case <-r.Context().Done():
		return
	case <-time.After(12 * time.Second):
		deny(503)
	}
}
