package consensus

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"sync"

	"github.com/hashicorp/raft"
)

const MaxDocument = 2 * 1024 * 1024
const MaxReceipts = 4096

// The Raft FSM is a bounded compare-and-swap of a prepared Catalog projection.
// Preparation validates ASC semantics in Python; apply has no clocks, random
// IDs, network IO, grants or jobs. Failed preconditions are committed receipts.
type Command struct {
	Schema        int    `json:"schema"`
	Cluster       string `json:"cluster_id"`
	Epoch         string `json:"epoch"`
	RequestID     string `json:"request_id"`
	Intent        string `json:"intent_sha256"`
	Expected      string `json:"expected_sha256"`
	Document      []byte `json:"document"`
	AuthorityTerm uint64 `json:"authority_term,omitempty"`
}
type Receipt struct {
	Digest string `json:"command_sha256"`
	Intent string `json:"intent_sha256"`
	Index  uint64 `json:"index"`
	Term   uint64 `json:"term"`
	SHA    string `json:"document_sha256"`
	Error  string `json:"error,omitempty"`
}
type State struct {
	Schema   int                `json:"schema"`
	Cluster  string             `json:"cluster_id"`
	Epoch    string             `json:"epoch"`
	Index    uint64             `json:"index"`
	Term     uint64             `json:"term"`
	Document []byte             `json:"document"`
	SHA      string             `json:"document_sha256"`
	Receipts map[string]Receipt `json:"receipts"`
}
type FSM struct {
	mu      sync.Mutex
	state   State
	binding string
}

func NewFSM(cluster, epoch string, seed []byte) *FSM {
	return &FSM{state: State{Schema: 1, Cluster: cluster, Epoch: epoch, Document: append([]byte{}, seed...), SHA: sum(seed), Receipts: map[string]Receipt{}}, binding: cluster + "/" + epoch}
}
func (f *FSM) View() State {
	f.mu.Lock()
	defer f.mu.Unlock()
	b, _ := json.Marshal(f.state)
	var s State
	json.Unmarshal(b, &s)
	return s
}
func (f *FSM) Apply(l *raft.Log) interface{} {
	f.mu.Lock()
	defer f.mu.Unlock()
	// HashiCorp can replay applied logs after restart. State and receipts are
	// recovered together from its snapshot, never from Python's ACK alone.
	if l.Index <= f.state.Index {
		return Receipt{Error: "applied_index_conflict"}
	}
	f.state.Index = l.Index
	f.state.Term = l.Term
	var c Command
	if len(l.Data) > 2*MaxDocument+4096 || json.Unmarshal(l.Data, &c) != nil || c.Schema != 1 || c.Cluster != f.state.Cluster || c.Epoch != f.state.Epoch || len(c.RequestID) < 8 || len(c.RequestID) > 128 || len(c.Document) > MaxDocument || !json.Valid(c.Document) {
		return Receipt{Error: "invalid_command"}
	}
	h := sum(l.Data)
	if previous, ok := f.state.Receipts[c.RequestID]; ok {
		if previous.Intent != c.Intent || (c.Intent == "" && previous.Digest != h) {
			return Receipt{Error: "request_id_conflict"}
		}
		return previous
	}
	if len(f.state.Receipts) >= MaxReceipts {
		return Receipt{Error: "receipt_limit"}
	}
	receipt := Receipt{Digest: h, Intent: c.Intent, Index: l.Index, Term: l.Term, SHA: f.state.SHA}
	var shape struct {
		Schema    int `json:"schema"`
		Authority struct {
			Term uint64 `json:"term"`
		} `json:"authority"`
	}
	json.Unmarshal(c.Document, &shape)
	var oldShape struct {
		Schema int `json:"schema"`
	}
	json.Unmarshal(f.state.Document, &oldShape)
	if (shape.Schema == 2 || oldShape.Schema == 2) && (c.AuthorityTerm == 0 || c.AuthorityTerm != l.Term || shape.Schema != 2 || shape.Authority.Term != l.Term) {
		receipt.Error = "stale_authority"
	} else if c.Expected != f.state.SHA {
		receipt.Error = "precondition_conflict"
	} else {
		var doc struct {
			Cluster  string `json:"cluster_id"`
			Epoch    string `json:"epoch"`
			Revision int64  `json:"revision"`
		}
		var previous struct {
			Revision int64 `json:"revision"`
		}
		json.Unmarshal(f.state.Document, &previous)
		if json.Unmarshal(c.Document, &doc) != nil || doc.Cluster != c.Cluster || doc.Epoch != c.Epoch ||
			(doc.Revision != previous.Revision+1 && !(doc.Revision == previous.Revision && bytes.Equal(c.Document, f.state.Document))) {
			receipt.Error = "invalid_projection"
		} else {
			f.state.Document = append([]byte{}, c.Document...)
			f.state.SHA = sum(c.Document)
			receipt.SHA = f.state.SHA
		}
	}
	f.state.Receipts[c.RequestID] = receipt
	return receipt
}
func (f *FSM) Snapshot() (raft.FSMSnapshot, error) {
	s := f.View()
	b, e := json.Marshal(s)
	return &fsmSnapshot{seal(b)}, e
}
func (f *FSM) Restore(r io.ReadCloser) error {
	defer r.Close()
	b, e := io.ReadAll(io.LimitReader(r, MaxFrame/2+1))
	if e != nil || len(b) > MaxFrame/2 {
		return ErrQuarantine
	}
	b, e = unseal(b)
	if e != nil {
		return e
	}
	var s State
	if json.Unmarshal(b, &s) != nil || s.Schema != 1 || s.Cluster+"/"+s.Epoch != f.binding || sum(s.Document) != s.SHA || len(s.Receipts) > MaxReceipts || s.Receipts == nil || len(s.Document) > MaxDocument || !json.Valid(s.Document) {
		return ErrQuarantine
	}
	for _, r := range s.Receipts {
		if r.Index == 0 || r.Index > s.Index || r.Term == 0 || r.Term > s.Term || len(r.Digest) != 64 || len(r.SHA) != 64 {
			return ErrQuarantine
		}
	}
	f.mu.Lock()
	defer f.mu.Unlock()
	if s.Index < f.state.Index {
		return errors.New("snapshot rollback")
	}
	f.state = s
	return nil
}

type fsmSnapshot struct{ bytes []byte }

func (s *fsmSnapshot) Persist(sink raft.SnapshotSink) error {
	if _, e := sink.Write(s.bytes); e != nil {
		sink.Cancel()
		return e
	}
	return sink.Close()
}
func (s *fsmSnapshot) Release() {}
