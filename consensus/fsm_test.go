package consensus

import (
	"bytes"
	"encoding/json"
	"io"
	"testing"

	"github.com/hashicorp/raft"
)

func TestFSMReceiptsCASAndSnapshot(t *testing.T) {
	seed := []byte(`{"cluster_id":"cluster-a","epoch":"epoch-a","revision":0}`)
	f := NewFSM("cluster-a", "epoch-a", seed)
	apply := func(index uint64, c Command) Receipt {
		b, e := json.Marshal(c)
		if e != nil {
			t.Fatal(e)
		}
		return f.Apply(&raft.Log{Index: index, Term: 1, Data: b}).(Receipt)
	}
	c := Command{Schema: 1, Cluster: "cluster-a", Epoch: "epoch-a", RequestID: "request-0001", Intent: sum([]byte("intent1")), Expected: sum(seed), Document: []byte(`{"cluster_id":"cluster-a","epoch":"epoch-a","revision":1}`)}
	one := apply(2, c)
	if one.Error != "" {
		t.Fatal(one.Error)
	}
	c.Expected = "changed-preparation"
	if replay := apply(3, c); replay != one {
		t.Fatal("semantic replay changed original receipt")
	}
	c.Intent = sum([]byte("different intent"))
	if r := apply(4, c); r.Error != "request_id_conflict" {
		t.Fatal("conflicting replay accepted")
	}
	c.RequestID = "request-0002"
	c.Expected = sum(seed)
	if r := apply(5, c); r.Error != "precondition_conflict" {
		t.Fatal("stale proposal accepted")
	}
	view := f.View()
	raw, e := json.Marshal(view)
	if e != nil {
		t.Fatal(e)
	}
	restored := NewFSM("cluster-a", "epoch-a", seed)
	if e = restored.Restore(io.NopCloser(bytes.NewReader(seal(raw)))); e != nil {
		t.Fatal(e)
	}
	if got := restored.View(); got.SHA != view.SHA || got.Index != view.Index || len(got.Receipts) != 2 {
		t.Fatal("snapshot lost applied checkpoint or receipts")
	}
	wrong := NewFSM("other-cluster", "epoch-a", seed)
	if e = wrong.Restore(io.NopCloser(bytes.NewReader(seal(raw)))); e == nil {
		t.Fatal("foreign snapshot accepted")
	}
	if e = restored.Restore(io.NopCloser(bytes.NewReader([]byte("corrupt")))); e == nil {
		t.Fatal("corrupt snapshot accepted")
	}
	for i := len(f.state.Receipts); i < MaxReceipts; i++ {
		f.state.Receipts[string(rune(i))] = Receipt{}
	}
	c.RequestID = "receipt-overflow"
	if r := apply(6, c); r.Error != "receipt_limit" {
		t.Fatal("receipt bound bypassed")
	}
}

func TestRuntimeAuthorityUsesActualCommittedTerm(t *testing.T) {
	seed := []byte(`{"schema":1,"cluster_id":"cluster-a","epoch":"epoch-a","revision":0}`)
	f := NewFSM("cluster-a", "epoch-a", seed)
	apply := func(index, term uint64, c Command) Receipt {
		b, e := json.Marshal(c)
		if e != nil {
			t.Fatal(e)
		}
		return f.Apply(&raft.Log{Index: index, Term: term, Data: b}).(Receipt)
	}
	c := Command{Schema: 1, Cluster: "cluster-a", Epoch: "epoch-a", RequestID: "runtime-upgrade-1", Intent: sum([]byte("upgrade")), Expected: sum(seed),
		AuthorityTerm: 3, Document: []byte(`{"schema":2,"cluster_id":"cluster-a","epoch":"epoch-a","revision":1,"authority":{"node_id":"a","term":3}}`)}
	if r := apply(2, 3, c); r.Error != "" {
		t.Fatal(r.Error)
	}
	before := f.View()
	c.RequestID = "delayed-old-term"
	c.Intent = sum([]byte("old"))
	c.Expected = before.SHA
	if r := apply(3, 4, c); r.Error != "stale_authority" {
		t.Fatal("old runtime term accepted", r)
	}
	c.RequestID = "self-asserted-high-term"
	c.AuthorityTerm = 1000
	if r := apply(4, 4, c); r.Error != "stale_authority" {
		t.Fatal("self asserted term accepted", r)
	}
	c.RequestID = "downgrade-to-metadata"
	c.AuthorityTerm = 0
	c.Document = []byte(`{"schema":1,"cluster_id":"cluster-a","epoch":"epoch-a","revision":2}`)
	if r := apply(5, 4, c); r.Error != "stale_authority" {
		t.Fatal("runtime downgrade accepted", r)
	}
	if got := f.View(); got.SHA != before.SHA {
		t.Fatal("denied authority changed document")
	}
	c.RequestID = "takeover-new-term"
	c.Intent = sum([]byte("takeover"))
	c.AuthorityTerm = 4
	c.Document = []byte(`{"schema":2,"cluster_id":"cluster-a","epoch":"epoch-a","revision":2,"authority":{"node_id":"b","term":4}}`)
	if r := apply(6, 4, c); r.Error != "" {
		t.Fatal(r.Error)
	}
	view := f.View()
	raw, _ := json.Marshal(view)
	restored := NewFSM("cluster-a", "epoch-a", seed)
	if e := restored.Restore(io.NopCloser(bytes.NewReader(seal(raw)))); e != nil {
		t.Fatal(e)
	}
	if got := restored.View(); got.SHA != view.SHA || !bytes.Equal(got.Document, c.Document) {
		t.Fatal("snapshot lost runtime authority")
	}
}

func TestBackupProjectionKeepsActualTermFencingAndSnapshotBytes(t *testing.T) {
	seed := []byte(`{"schema":1,"cluster_id":"cluster-a","epoch":"epoch-a","revision":0}`)
	f := NewFSM("cluster-a", "epoch-a", seed)
	apply := func(index, term uint64, c Command) Receipt {
		b, e := json.Marshal(c)
		if e != nil {
			t.Fatal(e)
		}
		return f.Apply(&raft.Log{Index: index, Term: term, Data: b}).(Receipt)
	}
	document := []byte(`{"schema":2,"cluster_id":"cluster-a","epoch":"epoch-a","revision":1,"authority":{"node_id":"a","term":3},"backup":{"schema":1,"snapshots":{"retained":{"source_index":10,"manifest_sha256":"retained-hash"}}}}`)
	c := Command{Schema: 1, Cluster: "cluster-a", Epoch: "epoch-a", RequestID: "backup-capture-001", Intent: sum([]byte("backup")), Expected: sum(seed), AuthorityTerm: 3, Document: document}
	if r := apply(11, 3, c); r.Error != "" {
		t.Fatal(r.Error)
	}
	before := f.View()
	c.RequestID = "backup-stale-delete"
	c.Expected = before.SHA
	c.Document = []byte(`{"schema":2,"cluster_id":"cluster-a","epoch":"epoch-a","revision":2,"authority":{"node_id":"a","term":3},"backup":{"schema":1,"snapshots":{}}}`)
	if r := apply(12, 4, c); r.Error != "stale_authority" {
		t.Fatal("stale backup delete accepted", r)
	}
	if !bytes.Equal(f.View().Document, document) {
		t.Fatal("stale backup changed retained manifest")
	}
	raw, _ := json.Marshal(f.View())
	restored := NewFSM("cluster-a", "epoch-a", seed)
	if e := restored.Restore(io.NopCloser(bytes.NewReader(seal(raw)))); e != nil {
		t.Fatal(e)
	}
	if !bytes.Equal(restored.View().Document, document) {
		t.Fatal("snapshot lost exact backup bytes")
	}
}
