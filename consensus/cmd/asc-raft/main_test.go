package main

import "testing"

func TestLauncherRejectsInvalidInvocation(t *testing.T) {
	for _, args := range [][]string{nil, {"reset"}, {"init"}, {"run", "--unknown"},
		{"run", "--config", "missing-private-config", "unexpected"}, {"init", "--config", "missing-private-config"}} {
		if run(args) {
			t.Fatal("invalid launcher invocation accepted")
		}
	}
}
