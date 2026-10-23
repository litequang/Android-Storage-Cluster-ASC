package consensus

import (
	"crypto/tls"
	"encoding/json"
	"io"
	"net"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/hashicorp/raft"
)

type testNode struct {
	r     *raft.Raft
	store *Store
	tr    *Transport
	fsm   *FSM
	dir   string
	cert  tls.Certificate
}
type testCluster struct {
	t     *testing.T
	peers []Peer
	nodes []*testNode
	seed  []byte
}

func newCluster(t *testing.T) *testCluster {
	t.Helper()
	c := &testCluster{t: t, seed: []byte(`{"cluster_id":"cluster-a","epoch":"epoch-a","revision":0}`)}
	listeners := make([]net.Listener, 3)
	for i, id := range []string{"a", "b", "c"} {
		cert, p, _ := testCert(t, id)
		ln, e := net.Listen("tcp", "127.0.0.1:0")
		if e != nil {
			t.Fatal(e)
		}
		listeners[i] = ln
		c.peers = append(c.peers, Peer{id, ln.Addr().String(), p})
		c.nodes = append(c.nodes, &testNode{dir: filepath.Join(t.TempDir(), "state"), cert: cert})
	}
	conf := raft.Configuration{}
	for _, p := range c.peers {
		conf.Servers = append(conf.Servers, raft.Server{ID: raft.ServerID(p.ID), Address: raft.ServerAddress(p.Address), Suffrage: raft.Voter})
	}
	for i, n := range c.nodes {
		if e := InitStore(n.dir, []byte("cluster-a/"+c.peers[i].ID), conf); e != nil {
			t.Fatal(e)
		}
		c.start(i, listeners[i])
	}
	t.Cleanup(func() {
		for i := range c.nodes {
			c.stop(i)
		}
	})
	return c
}
func (c *testCluster) start(i int, ln net.Listener) {
	c.t.Helper()
	n := c.nodes[i]
	var e error
	if ln == nil {
		ln, e = net.Listen("tcp", c.peers[i].Address)
		if e != nil {
			c.t.Fatal(e)
		}
	}
	n.store, e = OpenStore(n.dir, []byte("cluster-a/"+c.peers[i].ID))
	if e != nil {
		ln.Close()
		c.t.Fatal(e)
	}
	n.tr, e = NewTransport(c.peers[i].ID, "cluster-a", c.peers, n.cert, ln)
	if e != nil {
		c.t.Fatal(e)
	}
	n.fsm = NewFSM("cluster-a", "epoch-a", c.seed)
	snaps, e := raft.NewFileSnapshotStore(n.dir, 2, io.Discard)
	if e != nil {
		c.t.Fatal(e)
	}
	cfg := raft.DefaultConfig()
	cfg.LocalID = raft.ServerID(c.peers[i].ID)
	cfg.HeartbeatTimeout = 3 * time.Second
	cfg.ElectionTimeout = 6 * time.Second
	cfg.LeaderLeaseTimeout = 2 * time.Second
	cfg.CommitTimeout = 20 * time.Millisecond
	cfg.MaxAppendEntries = 1
	cfg.SnapshotThreshold = 8
	cfg.TrailingLogs = 2
	cfg.SnapshotInterval = 20 * time.Second
	cfg.LogOutput = io.Discard
	if os.Getenv("ASC_TEST_RAFT_DEBUG") == "1" {
		cfg.LogOutput = os.Stderr
	}
	n.r, e = raft.NewRaft(cfg, n.fsm, n.store, stableVotes{n.store}, snaps, n.tr)
	if e != nil {
		c.t.Fatal(e)
	}
}
func (c *testCluster) stop(i int) {
	n := c.nodes[i]
	if n.r != nil {
		n.r.Shutdown().Error()
		n.tr.Close()
		n.store.Close()
		n.r = nil
	}
}
func (c *testCluster) partition(i int, blocked bool) {
	for j, n := range c.nodes {
		if n.r == nil {
			continue
		}
		n.tr.mu.Lock()
		if j == i {
			for _, p := range c.peers {
				n.tr.blocked[p.ID] = blocked
			}
		} else {
			n.tr.blocked[c.peers[i].ID] = blocked
		}
		n.tr.mu.Unlock()
		n.tr.clientIdleClose()
	}
}
func (t *Transport) clientIdleClose() {
	for _, c := range t.clients {
		c.CloseIdleConnections()
	}
}
func (c *testCluster) leader(among ...int) int {
	c.t.Helper()
	deadline := time.Now().Add(45 * time.Second)
	for time.Now().Before(deadline) {
		found := -1
		for _, i := range among {
			if c.nodes[i].r != nil && c.nodes[i].r.State() == raft.Leader {
				if found != -1 {
					found = -1
					break
				}
				found = i
			}
		}
		if found >= 0 && c.nodes[found].r.VerifyLeader().Error() == nil {
			if e := c.nodes[found].r.Barrier(time.Second).Error(); e == nil {
				return found
			} else {
				c.t.Logf("leader barrier: %v", e)
			}
		}
		time.Sleep(30 * time.Millisecond)
	}
	for i, n := range c.nodes {
		if n.r != nil {
			c.t.Logf("node %d stats: %v", i, n.r.Stats())
		}
	}
	c.t.Fatal("no unique quorum-confirmed leader")
	return -1
}
func (c *testCluster) apply(i int, id string, revision int64) Receipt {
	c.t.Helper()
	s := c.nodes[i].fsm.View()
	doc, _ := json.Marshal(map[string]interface{}{"cluster_id": "cluster-a", "epoch": "epoch-a", "revision": revision, "marker": id})
	b, _ := json.Marshal(Command{Schema: 1, Cluster: "cluster-a", Epoch: "epoch-a", RequestID: id, Expected: s.SHA, Document: doc})
	f := c.nodes[i].r.Apply(b, time.Second)
	if e := f.Error(); e != nil {
		c.t.Fatal(e)
	}
	receipt := f.Response().(Receipt)
	if receipt.Error != "" {
		c.t.Fatal(receipt.Error)
	}
	return receipt
}
func (c *testCluster) waitRevision(i int, revision int64) {
	c.t.Helper()
	deadline := time.Now().Add(20 * time.Second)
	for time.Now().Before(deadline) {
		var d struct {
			Revision int64 `json:"revision"`
		}
		json.Unmarshal(c.nodes[i].fsm.View().Document, &d)
		if d.Revision == revision {
			return
		}
		time.Sleep(30 * time.Millisecond)
	}
	c.t.Fatalf("node %d did not reach revision %d", i, revision)
}

func TestQualificationClusterFaults(t *testing.T) {
	c := newCluster(t)
	leader := c.leader(0, 1, 2)
	c.apply(leader, "request-0001", 1)
	for i := range c.nodes {
		c.waitRevision(i, 1)
	}
	lagging := (leader + 1) % 3
	other := 3 - leader - lagging
	c.partition(lagging, true)
	c.apply(leader, "request-0002", 2) // 2/3 commit
	c.stop(leader)
	c.partition(lagging, false)
	next := c.leader(lagging, other)
	if next == lagging {
		t.Fatal("stale log defeated the fresher voter")
	}
	c.apply(next, "request-0003", 3)
	c.start(leader, nil)
	c.waitRevision(leader, 3)
	if c.nodes[leader].r.State() != raft.Follower {
		t.Fatal("old leader did not return as follower")
	}
	// Delay + repeated proposals exercise reordering/replay boundaries. The
	// upstream engine uses randomized wall-clock election timers; the fault
	// schedule and assertions are deterministic, not the exact elected ID.
	c.nodes[next].tr.mu.Lock()
	c.nodes[next].tr.delay = 40 * time.Millisecond
	c.nodes[next].tr.mu.Unlock()
	for rev := int64(4); rev <= 12; rev++ {
		c.apply(next, "request-"+time.Unix(rev, 0).UTC().Format("150405"), rev)
	}
	c.nodes[next].tr.mu.Lock()
	c.nodes[next].tr.delay = 0
	c.nodes[next].tr.mu.Unlock()
	for i := range c.nodes {
		c.waitRevision(i, 12)
	}
	// Deliver an earlier authenticated AppendEntries heartbeat AFTER a newer
	// committed command. Then replay it again: order/checkpoints cannot regress.
	lastIndex, e := c.nodes[next].store.LastIndex()
	if e != nil {
		t.Fatal(e)
	}
	var oldLog raft.Log
	if e = c.nodes[next].store.GetLog(lastIndex, &oldLog); e != nil {
		t.Fatal(e)
	}
	term, e := c.nodes[next].store.GetUint64([]byte("CurrentTerm"))
	if e != nil {
		t.Fatal(e)
	}
	oldHeartbeat := &raft.AppendEntriesRequest{RPCHeader: raft.RPCHeader{ProtocolVersion: raft.ProtocolVersionMax, ID: []byte(c.peers[next].ID), Addr: []byte(c.peers[next].Address)}, Term: term, PrevLogEntry: lastIndex, PrevLogTerm: oldLog.Term, LeaderCommitIndex: lastIndex}
	// Snapshot with an offline follower, compaction, then catch-up.
	catchup := (next + 1) % 3
	c.stop(catchup)
	for rev := int64(13); rev <= 20; rev++ {
		c.apply(next, "request-"+time.Unix(rev, 0).UTC().Format("150405"), rev)
	}
	online := 3 - next - catchup
	c.waitRevision(online, 20)
	for attempt := 0; attempt < 2; attempt++ {
		var response raft.AppendEntriesResponse
		if e = c.nodes[next].tr.AppendEntries(raft.ServerID(c.peers[online].ID), raft.ServerAddress(c.peers[online].Address), oldHeartbeat, &response); e != nil {
			t.Fatal(e)
		}
		c.waitRevision(online, 20)
	}
	if e := c.nodes[next].r.Snapshot().Error(); e != nil {
		t.Fatal(e)
	}
	c.start(catchup, nil)
	c.waitRevision(catchup, 20)
	// A minority cannot return success or a quorum read. It may retain an
	// uncommitted log entry; healing must converge without conflicting success.
	c.partition(next, true)
	minorityState := c.nodes[next].fsm.View()
	minorityDoc, _ := json.Marshal(map[string]interface{}{"cluster_id": "cluster-a", "epoch": "epoch-a", "revision": 21, "marker": "conflicting-minority-history"})
	minorityCommand, _ := json.Marshal(Command{Schema: 1, Cluster: "cluster-a", Epoch: "epoch-a", RequestID: "request-minority", Expected: minorityState.SHA, Document: minorityDoc})
	minorityFuture := c.nodes[next].r.Apply(minorityCommand, time.Second)
	majority := []int{}
	for i := range c.nodes {
		if i != next {
			majority = append(majority, i)
		}
	}
	newLeader := c.leader(majority...)
	c.apply(newLeader, "request-majority", 21)
	if e := minorityFuture.Error(); e == nil {
		t.Fatal("minority confirmed commit")
	}
	if e := c.nodes[next].r.VerifyLeader().Error(); e == nil {
		t.Fatal("minority confirmed strong read")
	}
	c.partition(next, false)
	for i := range c.nodes {
		c.waitRevision(i, 21)
	}
	// Full sidecar restart from durable logs/snapshots without bootstrap.
	for i := range c.nodes {
		c.stop(i)
	}
	for i := range c.nodes {
		c.start(i, nil)
	}
	last := c.leader(0, 1, 2)
	for i := range c.nodes {
		c.waitRevision(i, 21)
	}
	c.apply(last, "request-restart", 22)
	for i := range c.nodes {
		c.waitRevision(i, 22)
		s := c.nodes[i].fsm.View()
		if s.SHA != c.nodes[last].fsm.View().SHA {
			t.Fatal("conflicting committed histories")
		}
		if _, ok := s.Receipts["request-0001"]; !ok {
			t.Fatal("snapshot lost idempotency receipt")
		}
	}
}
