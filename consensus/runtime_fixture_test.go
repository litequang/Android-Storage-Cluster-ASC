package consensus

// This process fixture is linked only into `go test -c`, never asc-raft. It
// exposes the existing private transport fault schedule to the Python multi-
// process acceptance harness. Every file/address/credential is temporary.
import (
	"crypto/subtle"
	"encoding/json"
	"io"
	"net"
	"net/http"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/hashicorp/raft"
)

func TestMain(m *testing.M) {
	path := os.Getenv("ASC_TEST_RUNTIME_CONFIG")
	if path == "" {
		os.Exit(m.Run())
	}
	cfg, seed, e := ReadConfig(path)
	if e != nil {
		os.Exit(2)
	}
	n, e := Start(cfg, seed)
	if e != nil {
		os.Exit(3)
	}
	defer n.Close()
	var control struct {
		Address string `json:"address"`
		Token   string `json:"token"`
	}
	raw, e := os.ReadFile(os.Getenv("ASC_TEST_CONTROL_CONFIG"))
	if e != nil || len(raw) > 4096 || json.Unmarshal(raw, &control) != nil || !privateAddress(control.Address, true) || len(control.Token) < 43 {
		os.Exit(4)
	}
	listener, e := net.Listen("tcp", control.Address)
	if e != nil {
		os.Exit(5)
	}
	server := &http.Server{ReadHeaderTimeout: time.Second, ReadTimeout: 2 * time.Second, WriteTimeout: 2 * time.Second,
		Handler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.Method != "POST" || r.URL.Path != "/fault" || subtle.ConstantTimeCompare([]byte(r.Header.Get("Authorization")), []byte("Bearer "+control.Token)) != 1 {
				w.WriteHeader(403)
				return
			}
			var request struct {
				Blocked []string `json:"blocked"`
				Delay   int      `json:"delay_ms"`
			}
			b, e := io.ReadAll(http.MaxBytesReader(w, r.Body, 4096))
			if e != nil || json.Unmarshal(b, &request) != nil || len(request.Blocked) > 3 || request.Delay < 0 || request.Delay > 2000 {
				w.WriteHeader(400)
				return
			}
			for _, id := range request.Blocked {
				if _, ok := n.Transport.peers[id]; !ok || strings.Contains(id, "/") {
					w.WriteHeader(400)
					return
				}
			}
			n.Transport.mu.Lock()
			n.Transport.blocked = map[string]bool{}
			for _, id := range request.Blocked {
				n.Transport.blocked[id] = true
			}
			n.Transport.delay = time.Duration(request.Delay) * time.Millisecond
			n.Transport.mu.Unlock()
			w.Header().Set("Content-Type", "application/json")
			io.WriteString(w, `{"ok":true}`)
		})}
	go server.Serve(limitListener(listener, 4))
	defer server.Close()
	for n.Raft.State() != raft.Shutdown {
		time.Sleep(100 * time.Millisecond)
	}
}
