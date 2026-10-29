package consensus

import (
	"bytes"
	"io"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/hashicorp/raft"
	bbolt "go.etcd.io/bbolt"
)

func membership() raft.Configuration {
	return raft.Configuration{Servers: []raft.Server{
		{ID: "a", Address: "a", Suffrage: raft.Voter}, {ID: "b", Address: "b", Suffrage: raft.Voter}, {ID: "c", Address: "c", Suffrage: raft.Voter},
	}}
}

func TestQualificationLogRoundTrip(t *testing.T) {
	_, s := fixtureStore(t)
	defer s.Close()
	l := raft.Log{Index: 2, Term: 1, Type: raft.LogCommand, Data: []byte("abc"), AppendedAt: time.Now()}
	if e := s.StoreLog(&l); e != nil {
		t.Fatal(e)
	}
	var out raft.Log
	if e := s.GetLog(2, &out); e != nil {
		t.Fatalf("log round trip: %v; before=%#v; after=%#v", e, l, out)
	}
}
func fixtureStore(t *testing.T) (string, *Store) {
	t.Helper()
	dir := filepath.Join(t.TempDir(), "state")
	if e := InitStore(dir, []byte("cluster-a"), membership()); e != nil {
		t.Fatal(e)
	}
	s, e := OpenStore(dir, []byte("cluster-a"))
	if e != nil {
		t.Fatal(e)
	}
	return dir, s
}

func TestQualificationStableState(t *testing.T) {
	for _, damage := range []string{"none", "missing-db", "corrupt-db", "missing-term", "corrupt-term", "missing-vote", "missing-bucket", "partial-vote", "wrong-binding", "missing-anchor", "missing-log", "missing-snapshot-directory"} {
		t.Run(damage, func(t *testing.T) {
			dir, s := fixtureStore(t)
			if e := s.SetUint64([]byte("CurrentTerm"), 7); e != nil {
				t.Fatal(e)
			}
			if e := s.SetUint64([]byte("LastVoteTerm"), 7); e != nil {
				t.Fatal(e)
			}
			if e := (stableVotes{s}).Set([]byte("LastVoteCand"), []byte("b")); e != nil {
				t.Fatal(e)
			}
			if e := s.Close(); e != nil {
				t.Fatal(e)
			}
			path := filepath.Join(dir, "raft.db")
			switch damage {
			case "missing-snapshot-directory":
				if e := os.Remove(filepath.Join(dir, "snapshots")); e != nil {
					t.Fatal(e)
				}
			case "missing-db":
				if e := os.Remove(path); e != nil {
					t.Fatal(e)
				}
			case "corrupt-db":
				if e := os.WriteFile(path, []byte("invalid"), 0600); e != nil {
					t.Fatal(e)
				}
			case "missing-anchor":
				if e := os.Remove(filepath.Join(dir, "anchor", "binding")); e != nil {
					t.Fatal(e)
				}
			case "missing-term", "corrupt-term", "missing-vote", "missing-bucket", "partial-vote", "missing-log":
				db, e := bbolt.Open(path, 0600, nil)
				if e != nil {
					t.Fatal(e)
				}
				e = db.Update(func(tx *bbolt.Tx) error {
					b := tx.Bucket([]byte("conf"))
					switch damage {
					case "missing-term":
						return b.Delete([]byte("CurrentTerm"))
					case "corrupt-term":
						return b.Put([]byte("CurrentTerm"), []byte("bad"))
					case "missing-vote":
						return b.Delete([]byte("LastVoteCand"))
					case "missing-bucket":
						return tx.DeleteBucket([]byte("conf"))
					case "partial-vote":
						return b.Put([]byte("ASCVotePending"), seal([]byte{1}))
					case "missing-log":
						return tx.DeleteBucket([]byte("logs"))
					}
					return nil
				})
				ce := db.Close()
				if e != nil || ce != nil {
					t.Fatal(e, ce)
				}
			}
			binding := []byte("cluster-a")
			if damage == "wrong-binding" {
				binding = []byte("another-cluster")
			}
			s, e := OpenStore(dir, binding)
			if damage != "none" {
				if e == nil {
					s.Close()
					t.Fatal("damaged voter participated")
				}
				if damage == "missing-db" {
					if _, e = os.Stat(path); !os.IsNotExist(e) {
						t.Fatal("lost store recreated")
					}
				}
				return
			}
			if e != nil {
				t.Fatal(e)
			}
			defer s.Close()
			term, e := s.GetUint64([]byte("LastVoteTerm"))
			vote, ve := s.Get([]byte("LastVoteCand"))
			if e != nil || ve != nil || term != 7 || !bytes.Equal(vote, []byte("b")) {
				t.Fatal("vote not retained")
			}
		})
	}
}

type probeFSM struct{}

func (probeFSM) Apply(l *raft.Log) interface{}       { return string(l.Data) }
func (probeFSM) Snapshot() (raft.FSMSnapshot, error) { return probeSnapshot{}, nil }
func (probeFSM) Restore(r io.ReadCloser) error {
	defer r.Close()
	_, e := io.Copy(io.Discard, r)
	return e
}

type probeSnapshot struct{}

func (probeSnapshot) Persist(s raft.SnapshotSink) error {
	if _, e := s.Write([]byte("probe")); e != nil {
		s.Cancel()
		return e
	}
	return s.Close()
}
func (probeSnapshot) Release() {}

func TestQualificationNoDoubleVote(t *testing.T) {
	dir, s := fixtureStore(t)
	if e := s.SetUint64([]byte("CurrentTerm"), 7); e != nil {
		t.Fatal(e)
	}
	if e := s.SetUint64([]byte("LastVoteTerm"), 7); e != nil {
		t.Fatal(e)
	}
	if e := (stableVotes{s}).Set([]byte("LastVoteCand"), []byte("b")); e != nil {
		t.Fatal(e)
	}
	s.Close()
	s, e := OpenStore(dir, []byte("cluster-a"))
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	_, trans := raft.NewInmemTransport("a")
	defer trans.Close()
	_, caller := raft.NewInmemTransport("c")
	defer caller.Close()
	caller.Connect("a", trans)
	cfg := raft.DefaultConfig()
	cfg.LocalID = "a"
	cfg.HeartbeatTimeout = 10 * time.Second
	cfg.ElectionTimeout = 10 * time.Second
	cfg.LeaderLeaseTimeout = time.Second
	cfg.LogOutput = io.Discard
	snaps, e := raft.NewFileSnapshotStore(dir, 2, io.Discard)
	if e != nil {
		t.Fatal(e)
	}
	r, e := raft.NewRaft(cfg, probeFSM{}, s, stableVotes{s}, snaps, trans)
	if e != nil {
		t.Fatal(e)
	}
	defer func() { r.Shutdown().Error() }()
	request := &raft.RequestVoteRequest{RPCHeader: raft.RPCHeader{ProtocolVersion: raft.ProtocolVersionMax, ID: []byte("c"), Addr: []byte("c")}, Term: 7, LastLogIndex: 1, LastLogTerm: 1}
	var response raft.RequestVoteResponse
	if e = caller.RequestVote("a", "a", request, &response); e != nil {
		t.Fatal(e)
	}
	if response.Granted {
		t.Fatal("second same-term vote granted")
	}
	// A damaged live record must not enter upstream's defaultable not-found path.
	if e = s.BoltStore.Set([]byte("LastVoteCand"), []byte("corrupt live value")); e != nil {
		t.Fatal(e)
	}
	response = raft.RequestVoteResponse{}
	if e = caller.RequestVote("a", "a", request, &response); e != nil {
		t.Fatal(e)
	}
	if response.Granted || !s.IsQuarantined() {
		t.Fatal("live corrupt vote did not quarantine")
	}
	// Even repairing one record cannot resume a quarantined process.
	if e = s.BoltStore.Set([]byte("LastVoteCand"), seal([]byte("b"))); e != nil {
		t.Fatal(e)
	}
	if e = s.SetUint64([]byte("LastVoteTerm"), 8); e == nil {
		t.Fatal("quarantined voter resumed writes")
	}
}

func TestQualificationSnapshotCorruption(t *testing.T) {
	dir, s := fixtureStore(t)
	s.Close()
	snaps, e := raft.NewFileSnapshotStore(dir, 2, io.Discard)
	if e != nil {
		t.Fatal(e)
	}
	_, trans := raft.NewInmemTransport("a")
	defer trans.Close()
	sink, e := snaps.Create(1, 1, 1, membership(), 1, trans)
	if e != nil {
		t.Fatal(e)
	}
	fsm := NewFSM("cluster-a", "epoch-a", []byte(`{"cluster_id":"cluster-a","epoch":"epoch-a","revision":0}`))
	shot, e := fsm.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	defer shot.Release()
	if e = shot.Persist(sink); e != nil {
		t.Fatal(e)
	}
	valid, e := OpenStore(dir, []byte("cluster-a"))
	if e != nil {
		t.Fatal(e)
	}
	valid.Close()
	metas, e := snaps.List()
	if e != nil || len(metas) != 1 {
		t.Fatal("missing snapshot fixture", e)
	}
	if e = os.WriteFile(filepath.Join(dir, "snapshots", metas[0].ID, "state.bin"), []byte("corrupt snapshot"), 0600); e != nil {
		t.Fatal(e)
	}
	if opened, e := OpenStore(dir, []byte("cluster-a")); e == nil {
		opened.Close()
		t.Fatal("corrupt snapshot permitted participation")
	}
}

func TestQualificationMissingLiveStableKeyQuarantines(t *testing.T) {
	_, s := fixtureStore(t)
	defer s.Close()
	_, e := s.Get([]byte("missing-critical-stable-key"))
	if e == nil || e.Error() == "not found" || !s.IsQuarantined() {
		t.Fatal("stable loss remained a defaultable value")
	}
	if e = s.SetUint64([]byte("CurrentTerm"), 100); e == nil {
		t.Fatal("quarantined store accepted a new term")
	}
}
