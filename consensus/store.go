// ASC owns bootstrap/integrity policy; HashiCorp owns the Raft algorithm.
package consensus

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sync/atomic"
	"time"

	"github.com/hashicorp/raft"
	bolt "github.com/hashicorp/raft-boltdb/v2"
	bbolt "go.etcd.io/bbolt"
)

var ErrQuarantine = errors.New("durable state invalid: quarantine; restore reviewed complete state")

type Store struct {
	*bolt.BoltStore
	quarantined atomic.Bool
}
type sealed struct {
	Value []byte `json:"value"`
	SHA   string `json:"sha256"`
}

func sum(b []byte) string  { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }
func seal(b []byte) []byte { v, _ := json.Marshal(sealed{b, sum(b)}); return v }
func unseal(b []byte) ([]byte, error) {
	var v sealed
	if json.Unmarshal(b, &v) != nil || sum(v.Value) != v.SHA {
		return nil, ErrQuarantine
	}
	return v.Value, nil
}

// InitStore is explicit and exclusive. Runtime OpenStore NEVER creates state.
// Caller supplies the immutable cluster/node/membership/seed digest binding.
func InitStore(dir string, binding []byte, configuration raft.Configuration) error {
	if err := os.Mkdir(dir, 0700); err != nil {
		return err
	}
	s, err := bolt.New(bolt.Options{Path: filepath.Join(dir, "raft.db"), BoltOptions: &bbolt.Options{Timeout: time.Second}})
	if err != nil {
		return err
	}
	defer s.Close()
	g := &Store{BoltStore: s}
	for k, v := range map[string][]byte{"ASCBinding": binding, "CurrentTerm": make([]byte, 8), "LastVoteTerm": make([]byte, 8), "LastVoteCand": {}, "ASCVotePending": {0}} {
		if err = g.Set([]byte(k), v); err != nil {
			return err
		}
	}
	// Offline bootstrap writes the real upstream configuration entry, no listener.
	conf := raft.DefaultConfig()
	conf.LocalID = configuration.Servers[0].ID
	_, trans := raft.NewInmemTransport(configuration.Servers[0].Address)
	defer trans.Close()
	snaps, err := raft.NewFileSnapshotStore(dir, 2, os.Stderr)
	if err != nil {
		return err
	}
	if err = raft.BootstrapCluster(conf, g, g, snaps, trans, configuration); err != nil {
		return err
	}
	if err = os.Mkdir(filepath.Join(dir, "anchor"), 0700); err != nil {
		return err
	}
	// An incomplete explicit initialization remains non-runnable, never repaired.
	f, err := os.OpenFile(filepath.Join(dir, "anchor", "binding"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	if _, err = f.Write(seal(binding)); err == nil {
		err = f.Sync()
	}
	e := f.Close()
	if err == nil {
		err = e
	}
	return err
}

func OpenStore(dir string, binding []byte) (out *Store, err error) {
	// bbolt may panic for certain corrupt page layouts. No participation on panic.
	defer func() {
		if recover() != nil {
			out = nil
			err = ErrQuarantine
		}
	}()
	a, e := os.ReadFile(filepath.Join(dir, "anchor", "binding"))
	if e != nil {
		return nil, ErrQuarantine
	}
	b, e := unseal(a)
	if e != nil || !bytes.Equal(b, binding) {
		return nil, ErrQuarantine
	}
	path := filepath.Join(dir, "raft.db")
	info, e := os.Lstat(path)
	if e != nil || !info.Mode().IsRegular() {
		return nil, ErrQuarantine
	}
	// Inspect before the backend's CreateBucketIfNotExists can hide state loss.
	db, e := bbolt.Open(path, 0600, &bbolt.Options{ReadOnly: true, Timeout: time.Second})
	if e != nil {
		return nil, ErrQuarantine
	}
	// Also close on a corrupt-page panic caught by the outer quarantine guard.
	preflightOpen := true
	defer func() {
		if preflightOpen {
			db.Close()
		}
	}()
	e = db.View(func(tx *bbolt.Tx) error {
		if tx.Bucket([]byte("conf")) == nil || tx.Bucket([]byte("logs")) == nil {
			return ErrQuarantine
		}
		invalid := false
		for problem := range tx.Check() {
			if problem != nil {
				invalid = true
			}
		}
		if invalid {
			return ErrQuarantine
		}
		return nil
	})
	ce := db.Close()
	preflightOpen = false
	if e != nil || ce != nil {
		return nil, ErrQuarantine
	}
	s, e := bolt.New(bolt.Options{Path: path, BoltOptions: &bbolt.Options{Timeout: time.Second}})
	if e != nil {
		return nil, ErrQuarantine
	}
	g := &Store{BoltStore: s}
	ok := false
	defer func() {
		if !ok {
			s.Close()
		}
	}()
	b, e = g.Get([]byte("ASCBinding"))
	if e != nil || !bytes.Equal(b, binding) {
		return nil, ErrQuarantine
	}
	p, e := g.Get([]byte("ASCVotePending"))
	if e != nil || !bytes.Equal(p, []byte{0}) {
		return nil, fmt.Errorf("incomplete vote: %w", ErrQuarantine)
	}
	term, e := g.GetUint64([]byte("CurrentTerm"))
	if e != nil || term == 0 {
		return nil, fmt.Errorf("current term: %w", ErrQuarantine)
	}
	vt, e := g.GetUint64([]byte("LastVoteTerm"))
	if e != nil || vt > term {
		return nil, fmt.Errorf("vote term: %w", ErrQuarantine)
	}
	c, e := g.Get([]byte("LastVoteCand"))
	if e != nil || (vt > 0 && len(c) == 0) {
		return nil, fmt.Errorf("vote candidate: %w", ErrQuarantine)
	}
	first, e := g.FirstIndex()
	if e != nil {
		return nil, ErrQuarantine
	}
	last, e := g.LastIndex()
	if e != nil {
		return nil, ErrQuarantine
	}
	// Snapshots can compact all but a tail. Total log loss is quarantined rather
	// than guessed safe, even when a snapshot might permit manual recovery.
	if first == 0 || last < first || last-first > 1000000 {
		return nil, fmt.Errorf("log range: %w", ErrQuarantine)
	}
	// InstallSnapshot may leave an old retained prefix followed by a gap covered
	// by the new snapshot. Only a validated, fully read durable snapshot can
	// justify that gap; missing entries beyond it always quarantine.
	snapshotIndex := uint64(0)
	if st, e := os.Lstat(filepath.Join(dir, "snapshots")); e != nil || !st.IsDir() || st.Mode()&os.ModeSymlink != 0 {
		return nil, ErrQuarantine
	}
	snaps, e := raft.NewFileSnapshotStore(dir, 2, io.Discard)
	if e != nil {
		return nil, ErrQuarantine
	}
	metas, e := snaps.List()
	if e != nil {
		return nil, ErrQuarantine
	}
	if len(metas) > 0 {
		meta, reader, se := snaps.Open(metas[0].ID)
		if se != nil {
			return nil, ErrQuarantine
		}
		raw, re := io.ReadAll(io.LimitReader(reader, MaxFrame/2+1))
		ce := reader.Close()
		if re != nil || ce != nil || len(raw) > MaxFrame/2 {
			return nil, ErrQuarantine
		}
		raw, se = unseal(raw)
		var state State
		if se != nil || json.Unmarshal(raw, &state) != nil || sum(state.Document) != state.SHA || state.Index > meta.Index || state.Term > meta.Term || meta.Term > term {
			return nil, ErrQuarantine
		}
		snapshotIndex = meta.Index
	}
	if first > snapshotIndex+1 {
		return nil, fmt.Errorf("snapshot/log gap: %w", ErrQuarantine)
	}
	for i := first; i <= last; i++ {
		var l raft.Log
		if e := g.GetLog(i, &l); e != nil {
			if errors.Is(e, raft.ErrLogNotFound) && i <= snapshotIndex {
				continue
			}
			return nil, fmt.Errorf("log record %d: %w", i, e)
		}
		if l.Term > term {
			return nil, fmt.Errorf("log term: %w", ErrQuarantine)
		}
	}
	if st, e := os.Lstat(filepath.Join(dir, "snapshots")); e != nil || !st.IsDir() || st.Mode()&os.ModeSymlink != 0 {
		return nil, ErrQuarantine
	}
	ok = true
	return g, nil
}

func (s *Store) IsQuarantined() bool { return s.quarantined.Load() }
func (s *Store) failure(e error) error {
	if e != nil {
		s.quarantined.Store(true)
		return ErrQuarantine
	}
	return nil
}
func (s *Store) Set(k, v []byte) error {
	if s.IsQuarantined() {
		return ErrQuarantine
	}
	return s.failure(s.BoltStore.Set(k, seal(v)))
}
func (s *Store) Get(k []byte) ([]byte, error) {
	if s.IsQuarantined() {
		return nil, ErrQuarantine
	}
	b, e := s.BoltStore.Get(k)
	if e != nil {
		return nil, s.failure(e) // Never expose upstream's defaultable "not found".
	}
	b, e = unseal(b)
	if e != nil {
		return nil, s.failure(e)
	}
	return b, nil
}
func (s *Store) GetUint64(k []byte) (uint64, error) {
	b, e := s.Get(k)
	if e != nil || len(b) != 8 {
		return 0, s.failure(ErrQuarantine)
	}
	return binary.BigEndian.Uint64(b), nil
}
func (s *Store) SetUint64(k []byte, v uint64) error {
	if string(k) == "LastVoteTerm" {
		if err := s.Set([]byte("ASCVotePending"), []byte{1}); err != nil {
			return err
		}
	}
	b := make([]byte, 8)
	binary.BigEndian.PutUint64(b, v)
	return s.Set(k, b)
}

// Vote term and candidate are separate upstream StableStore calls. A crash in
// between is ambiguous: leave the durable pending marker and quarantine restart.
type stableVotes struct{ *Store }

func (s stableVotes) Set(k, v []byte) error {
	if err := s.Store.Set(k, v); err != nil {
		return err
	}
	if string(k) == "LastVoteCand" {
		return s.Store.Set([]byte("ASCVotePending"), []byte{0})
	}
	return nil
}

type logSeal struct {
	Extension []byte `json:"extension"`
	SHA       string `json:"sha256"`
}

func logHash(l raft.Log) string {
	l.AppendedAt = l.AppendedAt.UTC()
	b, _ := json.Marshal(l)
	return sum(b)
}
func (s *Store) StoreLog(l *raft.Log) error { return s.StoreLogs([]*raft.Log{l}) }
func (s *Store) StoreLogs(logs []*raft.Log) error {
	if s.IsQuarantined() {
		return ErrQuarantine
	}
	wrapped := make([]*raft.Log, len(logs))
	for i, l := range logs {
		copy := *l
		copy.Extensions, _ = json.Marshal(logSeal{l.Extensions, logHash(*l)})
		wrapped[i] = &copy
	}
	return s.failure(s.BoltStore.StoreLogs(wrapped))
}
func (s *Store) GetLog(i uint64, l *raft.Log) error {
	if s.IsQuarantined() {
		return ErrQuarantine
	}
	if err := s.BoltStore.GetLog(i, l); err != nil {
		if !errors.Is(err, raft.ErrLogNotFound) {
			return s.failure(err)
		}
		return err
	}
	var e logSeal
	if json.Unmarshal(l.Extensions, &e) != nil {
		return s.failure(ErrQuarantine)
	}
	l.Extensions = e.Extension
	if e.SHA != logHash(*l) {
		return s.failure(ErrQuarantine)
	}
	return nil
}
func (s *Store) FirstIndex() (uint64, error) {
	if s.IsQuarantined() {
		return 0, ErrQuarantine
	}
	v, e := s.BoltStore.FirstIndex()
	return v, s.failure(e)
}
func (s *Store) LastIndex() (uint64, error) {
	if s.IsQuarantined() {
		return 0, ErrQuarantine
	}
	v, e := s.BoltStore.LastIndex()
	return v, s.failure(e)
}
func (s *Store) DeleteRange(first, last uint64) error {
	if s.IsQuarantined() {
		return ErrQuarantine
	}
	return s.failure(s.BoltStore.DeleteRange(first, last))
}
