package consensus

import (
	"bytes"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/json"
	"encoding/pem"
	"io"
	"math/big"
	"net"
	"net/http"
	"testing"
	"time"

	"github.com/hashicorp/raft"
)

func testCert(t *testing.T, id string) (tls.Certificate, string, []byte) {
	t.Helper()
	key, e := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if e != nil {
		t.Fatal(e)
	}
	serial, e := rand.Int(rand.Reader, new(big.Int).Lsh(big.NewInt(1), 120))
	if e != nil {
		t.Fatal(e)
	}
	tmpl := &x509.Certificate{SerialNumber: serial, Subject: pkix.Name{CommonName: id}, NotBefore: time.Now().Add(-time.Hour), NotAfter: time.Now().Add(24 * time.Hour), IPAddresses: []net.IP{net.ParseIP("127.0.0.1")}, KeyUsage: x509.KeyUsageDigitalSignature | x509.KeyUsageCertSign, ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth, x509.ExtKeyUsageServerAuth}, IsCA: true, BasicConstraintsValid: true}
	der, e := x509.CreateCertificate(rand.Reader, tmpl, tmpl, &key.PublicKey, key)
	if e != nil {
		t.Fatal(e)
	}
	certPEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})
	kb, e := x509.MarshalPKCS8PrivateKey(key)
	if e != nil {
		t.Fatal(e)
	}
	kp := pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: kb})
	cert, e := tls.X509KeyPair(certPEM, kp)
	if e != nil {
		t.Fatal(e)
	}
	return cert, string(certPEM), kp
}

func TestQualificationPeerAuthentication(t *testing.T) {
	peers := make([]Peer, 3)
	certs := make([]tls.Certificate, 3)
	listeners := make([]net.Listener, 3)
	for i, id := range []string{"a", "b", "c"} {
		cert, p, _ := testCert(t, id)
		certs[i] = cert
		ln, e := net.Listen("tcp", "127.0.0.1:0")
		if e != nil {
			t.Fatal(e)
		}
		listeners[i] = ln
		peers[i] = Peer{id, ln.Addr().String(), p}
	}
	trans := make([]*Transport, 3)
	for i := range peers {
		tr, e := NewTransport(peers[i].ID, "cluster-a", peers, certs[i], listeners[i])
		if e != nil {
			t.Fatal(e)
		}
		trans[i] = tr
		defer tr.Close()
	}
	q := &raft.RequestVoteRequest{RPCHeader: raft.RPCHeader{ProtocolVersion: raft.ProtocolVersionMax, ID: []byte("b"), Addr: []byte(peers[1].Address)}, Term: 9}
	done := make(chan error, 1)
	go func() {
		var r raft.RequestVoteResponse
		done <- trans[1].RequestVote("a", raft.ServerAddress(peers[0].Address), q, &r)
	}()
	select {
	case rpc := <-trans[0].Consumer():
		rpc.Respond(&raft.RequestVoteResponse{Granted: true}, nil)
	case <-time.After(5 * time.Second):
		t.Fatal("authenticated RPC never arrived")
	}
	if e := <-done; e != nil {
		t.Fatal(e)
	}
	// A valid b certificate claiming c must be denied before engine dispatch.
	q.ID = []byte("c")
	q.Addr = []byte(peers[2].Address)
	var r raft.RequestVoteResponse
	if e := trans[1].RequestVote("a", raft.ServerAddress(peers[0].Address), q, &r); e == nil {
		t.Fatal("peer spoof accepted")
	}
	select {
	case <-trans[0].Consumer():
		t.Fatal("spoof reached Raft")
	default:
	}
	// Unknown certificate and no certificate both fail ordinary TLS verification.
	unknown, _, _ := testCert(t, "outsider")
	roots := x509.NewCertPool()
	roots.AppendCertsFromPEM([]byte(peers[0].Certificate))
	for _, certs := range [][]tls.Certificate{nil, {unknown}} {
		client := &http.Client{Transport: &http.Transport{TLSClientConfig: &tls.Config{RootCAs: roots, Certificates: certs, MinVersion: tls.VersionTLS13}}, Timeout: 2 * time.Second}
		b, _ := json.Marshal(rpcFrame{Request: []byte(`{}`)})
		resp, e := client.Post("https://"+peers[0].Address+"/raft/v1/vote", "application/json", bytes.NewReader(b))
		if e == nil {
			io.Copy(io.Discard, resp.Body)
			resp.Body.Close()
			t.Fatal("unauthorized TLS peer accepted")
		}
		client.CloseIdleConnections()
	}
}
