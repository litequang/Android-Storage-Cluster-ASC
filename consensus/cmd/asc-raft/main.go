// asc-raft is the explicit development launcher for the existing consensus APIs.
package main

import (
	"context"
	"flag"
	"fmt"
	"io"
	"os"
	"os/signal"
	"runtime"
	"syscall"
	"time"

	"github.com/hashicorp/raft"
	consensus "github.com/litequang/Android-Storage-Cluster-ASC/consensus"
)

func run(args []string) bool {
	if runtime.GOOS == "android" || len(args) == 0 || (args[0] != "init" && args[0] != "run") {
		return false
	}
	flags := flag.NewFlagSet("asc-raft", flag.ContinueOnError)
	flags.SetOutput(io.Discard)
	path := flags.String("config", "", "private configuration file")
	if flags.Parse(args[1:]) != nil || *path == "" || flags.NArg() != 0 {
		return false
	}
	cfg, seed, err := consensus.ReadConfig(*path)
	if err != nil {
		return false
	}
	if args[0] == "init" {
		return cfg.Initialize() == nil
	}
	node, err := consensus.Start(cfg, seed)
	if err != nil {
		return false
	}
	defer node.Close()
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()
	tick := time.NewTicker(100 * time.Millisecond)
	defer tick.Stop()
	for node.Raft.State() != raft.Shutdown {
		select {
		case <-ctx.Done():
			return true
		case <-tick.C:
		}
	}
	return true
}

func main() {
	if !run(os.Args[1:]) {
		fmt.Fprintln(os.Stderr, "ASC sidecar refused; preserve private state and consult GO-SIDECAR.md")
		os.Exit(1)
	}
}
