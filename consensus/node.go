package consensus

import (
	"bytes"
	"context"
	"crypto/sha256"
	"crypto/subtle"
	"crypto/tls"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strconv"
	"sync"
	"time"

	"github.com/hashicorp/raft"
)

type Config struct {
	Schema     int    `json:"schema"`
	Cluster    string `json:"cluster_id"`
	Epoch      string `json:"epoch"`
	NodeID     string `json:"node_id"`
	Peers      []Peer `json:"peers"`
	StateDir   string `json:"state_dir"`
	SeedFile   string `json:"seed_file"`
	SeedSHA    string `json:"seed_sha256"`
	CertFile   string `json:"cert_file"`
	KeyFile    string `json:"key_file"`
	IPCAddress string `json:"ipc_address"`
	IPCToken   string `json:"ipc_token"`
}

func ReadConfig(path string) (Config, []byte, error) {
	var cfg Config
	b, e := os.ReadFile(path)
	if e != nil || len(b) > 64*1024 {
		return cfg, nil, errors.New("config unavailable")
	}
	d := json.NewDecoder(bytes.NewReader(b))
	d.DisallowUnknownFields()
	if d.Decode(&cfg) != nil || d.Decode(new(interface{})) != io.EOF {
		return cfg, nil, errors.New("invalid config")
	}
	if cfg.Schema != 1 || cfg.Cluster == "" || cfg.Epoch == "" || cfg.NodeID == "" || len(cfg.IPCToken) < 43 || len(cfg.IPCToken) > 128 || len(cfg.Peers) != 3 || !filepath.IsAbs(cfg.StateDir) || !filepath.IsAbs(cfg.SeedFile) || !filepath.IsAbs(cfg.CertFile) || !filepath.IsAbs(cfg.KeyFile) {
		return cfg, nil, errors.New("invalid config")
	}
	if !privateAddress(cfg.IPCAddress, true) {
		return cfg, nil, errors.New("IPC must bind numeric loopback")
	}
	seenID, seenAddr := map[string]bool{}, map[string]bool{}
	own := false
	for _, p := range cfg.Peers {
		if p.ID == "" || seenID[p.ID] || seenAddr[p.Address] || !privateAddress(p.Address, false) {
			return cfg, nil, errors.New("invalid static membership")
		}
		seenID[p.ID] = true
		seenAddr[p.Address] = true
		if p.ID == cfg.NodeID {
			own = true
		}
	}
	if !own {
		return cfg, nil, errors.New("local voter missing")
	}
	for _, path := range []string{path, cfg.StateDir, cfg.SeedFile, cfg.CertFile, cfg.KeyFile} {
		if insideCheckout(path) {
			return cfg, nil, errors.New("private consensus files must be outside source checkout")
		}
	}
	seed, e := os.ReadFile(cfg.SeedFile)
	if e != nil || len(seed) > MaxDocument || sum(seed) != cfg.SeedSHA || !json.Valid(seed) {
		return cfg, nil, errors.New("seed integrity mismatch")
	}
	var doc struct {
		Cluster string `json:"cluster_id"`
		Epoch   string `json:"epoch"`
	}
	if json.Unmarshal(seed, &doc) != nil || doc.Cluster != cfg.Cluster || doc.Epoch != cfg.Epoch {
		return cfg, nil, errors.New("seed identity mismatch")
	}
	return cfg, seed, nil
}
func privateAddress(address string, loopback bool) bool {
	host, port, e := net.SplitHostPort(address)
	portNumber, pe := strconv.Atoi(port)
	if e != nil || pe != nil || portNumber < 1024 || portNumber > 65535 {
		return false
	}
	ip := net.ParseIP(host)
	return ip != nil && !ip.IsUnspecified() && !ip.IsMulticast() && (ip.IsLoopback() || !loopback && ip.IsPrivate())
}
func insideCheckout(path string) bool {
	for dir := filepath.Dir(path); ; dir = filepath.Dir(dir) {
		if _, e := os.Stat(filepath.Join(dir, ".git")); e == nil {
			return true
		}
		if filepath.Dir(dir) == dir {
			return false
		}
	}
}
func (c Config) configuration() raft.Configuration {
	conf := raft.Configuration{}
	for _, p := range c.Peers {
		conf.Servers = append(conf.Servers, raft.Server{ID: raft.ServerID(p.ID), Address: raft.ServerAddress(p.Address), Suffrage: raft.Voter})
	}
	return conf
}
func (c Config) Binding() []byte {
	peers := append([]Peer{}, c.Peers...)
	sort.Slice(peers, func(i, j int) bool { return peers[i].ID < peers[j].ID })
	b, _ := json.Marshal(struct {
		Schema                          int
		Cluster, Epoch, NodeID, SeedSHA string
		Peers                           []Peer
	}{1, c.Cluster, c.Epoch, c.NodeID, c.SeedSHA, peers})
	return b
}
func (c Config) Initialize() error {
	if _, e := os.Lstat(c.StateDir); !os.IsNotExist(e) {
		return ErrQuarantine
	}
	// A separate enrollment witness survives loss of the whole Raft directory.
	// No init/run path may overwrite it or silently reuse an enrolled identity.
	f, e := os.OpenFile(c.StateDir+".enrolled", os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if e != nil {
		return ErrQuarantine
	}
	_, e = f.Write(seal(c.Binding()))
	if e == nil {
		e = f.Sync()
	}
	ce := f.Close()
	if e != nil || ce != nil {
		return ErrQuarantine
	}
	return InitStore(c.StateDir, c.Binding(), c.configuration())
}

type Node struct {
	Raft      *raft.Raft
	FSM       *FSM
	Store     *Store
	Transport *Transport
	cfg       Config
	ipc       *http.Server
	slots     chan struct{}
	closed    sync.Once
}

func Start(cfg Config, seed []byte) (*Node, error) {
	if runtime.GOOS == "android" {
		return nil, errors.New("Android runtime is not qualified")
	}
	if st, e := os.Lstat(cfg.StateDir); e != nil || !st.IsDir() || st.Mode()&os.ModeSymlink != 0 {
		return nil, ErrQuarantine
	}
	witness, e := os.ReadFile(cfg.StateDir + ".enrolled")
	if e != nil {
		return nil, ErrQuarantine
	}
	binding, e := unseal(witness)
	if e != nil || !bytes.Equal(binding, cfg.Binding()) {
		return nil, ErrQuarantine
	}
	s, e := OpenStore(cfg.StateDir, cfg.Binding())
	if e != nil {
		return nil, e
	}
	n := &Node{cfg: cfg, Store: s, FSM: NewFSM(cfg.Cluster, cfg.Epoch, seed), slots: make(chan struct{}, 8)}
	ok := false
	defer func() {
		if !ok {
			n.Close()
		}
	}()
	vt, e := s.GetUint64([]byte("LastVoteTerm"))
	if e != nil {
		return nil, ErrQuarantine
	}
	if vt > 0 {
		vote, e := s.Get([]byte("LastVoteCand"))
		known := false
		for _, p := range cfg.Peers {
			known = known || string(vote) == p.Address
		}
		if e != nil || !known {
			return nil, ErrQuarantine
		}
	}
	cert, e := tls.LoadX509KeyPair(cfg.CertFile, cfg.KeyFile)
	if e != nil {
		return nil, errors.New("local TLS identity unavailable")
	}
	var addr string
	for _, p := range cfg.Peers {
		if p.ID == cfg.NodeID {
			addr = p.Address
		}
	}
	ln, e := net.Listen("tcp", addr)
	if e != nil {
		return nil, errors.New("peer listener unavailable")
	}
	n.Transport, e = NewTransport(cfg.NodeID, cfg.Cluster, cfg.Peers, cert, ln, s.IsQuarantined)
	if e != nil {
		ln.Close()
		return nil, e
	}
	snaps, e := raft.NewFileSnapshotStore(cfg.StateDir, 2, io.Discard)
	if e != nil {
		return nil, e
	}
	// Snapshot membership must match the immutable static three-voter config.
	metas, e := snaps.List()
	if e != nil {
		return nil, e
	}
	for _, m := range metas {
		if !sameMembership(m.Configuration, cfg.configuration()) {
			return nil, ErrQuarantine
		}
	}
	c := raft.DefaultConfig()
	c.LocalID = raft.ServerID(cfg.NodeID)
	c.HeartbeatTimeout = 3 * time.Second
	c.ElectionTimeout = 6 * time.Second
	c.LeaderLeaseTimeout = 2 * time.Second
	c.CommitTimeout = 50 * time.Millisecond
	c.MaxAppendEntries = 1
	c.TrailingLogs = 32
	c.SnapshotThreshold = 64
	c.SnapshotInterval = 30 * time.Second
	c.LogOutput = io.Discard
	n.Raft, e = raft.NewRaft(c, n.FSM, s, stableVotes{s}, snaps, n.Transport)
	if e != nil {
		return nil, e
	}
	if !sameMembership(n.Raft.GetConfiguration().Configuration(), cfg.configuration()) {
		return nil, ErrQuarantine
	}
	ipc, e := net.Listen("tcp", cfg.IPCAddress)
	if e != nil {
		return nil, errors.New("IPC listener unavailable")
	}
	n.ipc = &http.Server{Handler: n, ReadHeaderTimeout: time.Second, ReadTimeout: 15 * time.Second, WriteTimeout: 20 * time.Second, IdleTimeout: 3 * time.Second, MaxHeaderBytes: 4096, ErrorLog: log.New(io.Discard, "", 0)}
	go n.ipc.Serve(limitListener(ipc, 16))
	ok = true
	return n, nil
}
func sameMembership(a, b raft.Configuration) bool {
	aa := map[raft.ServerID]raft.Server{}
	for _, s := range a.Servers {
		aa[s.ID] = s
	}
	if len(a.Servers) != len(b.Servers) {
		return false
	}
	for _, s := range b.Servers {
		if aa[s.ID] != s {
			return false
		}
	}
	return true
}
func (n *Node) Close() {
	n.closed.Do(func() {
		if n.ipc != nil {
			n.ipc.Close()
		}
		if n.Raft != nil {
			n.Raft.Shutdown().Error()
		}
		if n.Transport != nil {
			n.Transport.Close()
		}
		if n.Store != nil {
			n.Store.Close()
		}
	})
}
func future(ctx context.Context, f raft.Future) error {
	done := make(chan error, 1)
	go func() { done <- f.Error() }()
	select {
	case e := <-done:
		return e
	case <-ctx.Done():
		return ctx.Err()
	}
}
func (n *Node) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	reply := func(status int, v interface{}) { w.WriteHeader(status); json.NewEncoder(w).Encode(v) }
	deny := func(status int, label string) {
		_, id := n.Raft.LeaderWithID()
		reply(status, map[string]interface{}{"error": label, "leader_id": id})
	}
	want := sha256.Sum256([]byte("Bearer " + n.cfg.IPCToken))
	got := sha256.Sum256([]byte(r.Header.Get("Authorization")))
	if subtle.ConstantTimeCompare(want[:], got[:]) != 1 {
		deny(401, "ipc_unauthorized")
		return
	}
	select {
	case n.slots <- struct{}{}:
		defer func() { <-n.slots }()
	default:
		deny(429, "ipc_busy")
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 15*time.Second)
	defer cancel()
	if n.Store.IsQuarantined() && r.URL.Path != "/v1/status" && r.URL.Path != "/v1/shutdown" {
		deny(503, "voter_quarantined")
		return
	}
	switch {
	case r.Method == "GET" && r.URL.Path == "/v1/status":
		_, leader := n.Raft.LeaderWithID()
		s := n.FSM.View()
		reply(200, map[string]interface{}{"schema": 1, "cluster_id": n.cfg.Cluster, "node_id": n.cfg.NodeID, "leader_id": leader, "role": n.Raft.State().String(), "term": n.Raft.Stats()["term"], "applied_index": s.Index, "document_sha256": s.SHA, "metadata_only": true, "static_voters": 3, "quarantined": n.Store.IsQuarantined()})
	case r.Method == "GET" && r.URL.Path == "/v1/state":
		consistency := r.URL.Query().Get("consistency")
		if consistency != "local" && consistency != "strong" {
			deny(400, "invalid_consistency")
			return
		}
		if consistency == "strong" {
			if e := future(ctx, n.Raft.Barrier(5*time.Second)); e != nil {
				deny(503, "quorum_read_unavailable")
				return
			}
		}
		reply(200, map[string]interface{}{"state": n.FSM.View(), "stale": consistency != "strong", "read_only": true})
	case r.Method == "POST" && r.URL.Path == "/v1/commands":
		b, e := io.ReadAll(http.MaxBytesReader(w, r.Body, 2*MaxDocument+4096))
		if e != nil {
			deny(413, "command_limit")
			return
		}
		var c Command
		d := json.NewDecoder(bytes.NewReader(b))
		d.DisallowUnknownFields()
		if d.Decode(&c) != nil || d.Decode(new(interface{})) != io.EOF || c.Schema != 1 || c.Cluster != n.cfg.Cluster || c.Epoch != n.cfg.Epoch || len(c.Intent) != 64 || len(c.Document) > MaxDocument {
			deny(400, "invalid_command")
			return
		}
		if _, e := hex.DecodeString(c.Intent); e != nil {
			deny(400, "invalid_intent")
			return
		}
		f := n.Raft.Apply(b, 5*time.Second)
		if e = future(ctx, f); e != nil {
			deny(503, "commit_unconfirmed")
			return
		}
		receipt, ok := f.Response().(Receipt)
		if !ok {
			deny(503, "apply_unavailable")
			return
		}
		if receipt.Error != "" {
			reply(409, map[string]interface{}{"error": receipt.Error, "receipt": receipt})
			return
		}
		reply(200, map[string]interface{}{"receipt": receipt})
	case r.Method == "POST" && r.URL.Path == "/v1/snapshot":
		if e := future(ctx, n.Raft.Snapshot()); e != nil {
			deny(503, "snapshot_unavailable")
			return
		}
		reply(200, map[string]bool{"ok": true})
	case r.Method == "POST" && r.URL.Path == "/v1/shutdown":
		reply(200, map[string]bool{"ok": true})
		go func() { time.Sleep(100 * time.Millisecond); n.Close() }()
	default:
		deny(404, "unsupported_operation")
	}
}
