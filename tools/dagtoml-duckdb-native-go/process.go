package main

import (
	"bytes"
	"errors"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"
)

const maxCommandOutput = 8 * 1024 * 1024

type commandRecord struct {
	pid         int
	Arguments   []string `json:"command"`
	Environment []string `json:"environment"`
	Directory   string   `json:"cwd"`
	Stdout      []byte   `json:"stdout_base64"`
	Stderr      []byte   `json:"stderr_base64"`
	ExitCode    int      `json:"exit_code"`
	Failure     string   `json:"failure,omitempty"`
}

type commandStream struct {
	name string
	data []byte
	err  error
}

func commandRun(directory string, arguments []string, deadline time.Duration) (record commandRecord, resultErr error) {
	record = commandRecord{Arguments: append([]string{}, arguments...), Directory: directory, ExitCode: -1}
	if len(arguments) == 0 || !absolute(arguments[0]) || deadline <= 0 || deadline > 10*time.Minute {
		return record, errors.New("compiler command requires an absolute executable and bounded deadline")
	}
	command := exec.Command(arguments[0], arguments[1:]...) // #nosec G204 -- Authored compiler vectors use no shell and accept no document data.
	command.Dir = directory
	// Compiler search paths and Python imports must not inherit caller overrides.
	command.Env = []string{"PATH=/usr/bin:/bin", "LC_ALL=C", "TMPDIR=" + directory}
	record.Environment = append([]string{}, command.Env...)
	command.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
	stdout, err := command.StdoutPipe()
	if err != nil {
		return record, err
	}
	stderr, err := command.StderrPipe()
	if err != nil {
		return record, errors.Join(err, stdout.Close())
	}
	if err = command.Start(); err != nil {
		return record, errors.Join(err, stdout.Close(), stderr.Close())
	}
	record.pid = command.Process.Pid
	streams := make(chan commandStream, 2)
	seen := map[string]bool{}
	save := func(stream commandStream) error {
		if seen[stream.name] || (stream.name != "stdout" && stream.name != "stderr") {
			return errors.New("compiler stream population is invalid")
		}
		seen[stream.name] = true
		if stream.name == "stdout" {
			record.Stdout = stream.data
		} else {
			record.Stderr = stream.data
		}
		return nil
	}
	// Keep the direct child unreaped until its process group is abandoned.
	// Its PID therefore continues to reserve the group identity during cleanup.
	defer func() {
		killErr := syscall.Kill(-command.Process.Pid, syscall.SIGKILL)
		if errors.Is(killErr, syscall.ESRCH) {
			killErr = nil
		}
		closeOut, closeError := stdout.Close(), stderr.Close()
		if errors.Is(closeOut, os.ErrClosed) {
			closeOut = nil
		}
		if errors.Is(closeError, os.ErrClosed) {
			closeError = nil
		}
		waitErr := command.Wait()
		if command.ProcessState != nil {
			record.ExitCode = command.ProcessState.ExitCode()
		}
		if record.Failure == "" && waitErr != nil {
			record.Failure = "exit-status"
		}
		resultErr = errors.Join(resultErr, killErr, closeOut, closeError, waitErr)
		cleanupTimer := time.NewTimer(time.Second)
		defer cleanupTimer.Stop()
		for len(seen) < 2 {
			select {
			case stream := <-streams:
				resultErr = errors.Join(resultErr, save(stream))
			case <-cleanupTimer.C:
				resultErr = errors.Join(resultErr, errors.New("compiler stream cleanup did not complete"))
				record.Failure = "stream-cleanup"
				return
			}
		}
		if record.Failure == "" && resultErr != nil {
			record.Failure = "cleanup"
		}
	}()
	read := func(name string, reader io.Reader) {
		data, err := io.ReadAll(io.LimitReader(reader, maxCommandOutput+1))
		streams <- commandStream{name, data, err}
	}
	go read("stdout", stdout)
	go read("stderr", stderr)
	timer := time.NewTimer(deadline)
	defer timer.Stop()
	poll := time.NewTicker(10 * time.Millisecond)
	defer poll.Stop()
	exited := false
	for len(seen) < 2 || !exited {
		select {
		case stream := <-streams:
			if err := save(stream); err != nil {
				record.Failure = "stream-identity"
				return record, err
			}
			if stream.err != nil {
				record.Failure = "stream-read"
				return record, errors.New("compiler stream is incomplete")
			}
			if len(stream.data) > maxCommandOutput {
				record.Failure = "output-limit"
				return record, errors.New("compiler output exceeded its bound")
			}
		case <-poll.C:
			exited, err = commandExited(command.Process.Pid)
			if err != nil {
				record.Failure = "process-state"
				return record, err
			}
		case <-timer.C:
			record.Failure = "deadline"
			return record, errors.New("compiler operation exceeded its deadline")
		}
	}
	return record, nil
}

// Observe completion without reaping the PID that reserves the owned group.
func commandExited(pid int) (bool, error) {
	body, err := os.ReadFile(filepath.Join("/proc", strconv.Itoa(pid), "stat")) // #nosec G304 -- The command's own unreaped numeric PID, not a caller-supplied path.
	if err != nil {
		return false, err
	}
	at := bytes.LastIndexByte(body, ')')
	if at < 0 {
		return false, errors.New("owned compiler process state is malformed")
	}
	fields := strings.Fields(string(body[at+1:]))
	if len(fields) == 0 || len(fields[0]) != 1 {
		return false, errors.New("owned compiler process state is absent")
	}
	return fields[0] == "Z" || fields[0] == "X", nil
}
