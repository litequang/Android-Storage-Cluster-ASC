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
