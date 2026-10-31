package main

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"
)

func instrumentProducer(mode string) error {
	switch mode {
	case "normal":
		_, outErr := os.Stdout.Write([]byte("accepted-output"))
		_, errorErr := os.Stderr.Write([]byte("accepted-diagnostic"))
		return errors.Join(outErr, errorErr)
	case "environment":
		_, err := fmt.Fprint(os.Stdout, strings.Join([]string{os.Getenv("GOTOOLCHAIN"), os.Getenv("CGO_ENABLED"), os.Getenv("GOWORK"), os.Getenv("GOOS"), os.Getenv("GOARCH"), os.Getenv("GOAMD64"), os.Getenv("GOEXPERIMENT"), os.Getenv("GOFLAGS")}, "|"))
		return err
	case "closed-streams":
		if len(os.Args) != 3 {
			return errors.New("closed-stream control marker is absent")
		}
		if err := errors.Join(os.Stdout.Close(), os.Stderr.Close()); err != nil {
			return err
		}
		time.Sleep(50 * time.Millisecond)
		marker, err := os.OpenFile("closed-stream-completed", os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if err != nil {
			return err
		}
		_, writeErr := marker.Write([]byte("completed"))
		return errors.Join(writeErr, marker.Close())
	case "overflow":
		_, err := os.Stdout.Write(bytes.Repeat([]byte{'x'}, maxCommandOutput+1))
		return err
	case "deadline":
		time.Sleep(5 * time.Second)
		return nil
	case "descendant":
		executable, err := os.Executable()
		if err != nil {
			return err
		}
		child := exec.Command(executable, "--instrument-producer", "deadline") // #nosec G204 -- The current self-check executable and fixed internal arguments.
		child.Stdout, child.Stderr = os.Stdout, os.Stderr
		if err = child.Start(); err != nil {
			return err
		}
		if _, err = fmt.Fprint(os.Stdout, child.Process.Pid); err != nil {
			return err
		}
		return child.Process.Release()
	default:
		return errors.New("unknown control producer")
	}
}

func processControls(work string) (resultErr error) {
	previous, present := os.LookupEnv("GOFLAGS")
	if err := os.Setenv("GOFLAGS", "-injected-caller-flag"); err != nil {
		return err
	}
	defer func() {
		if present {
			resultErr = errors.Join(resultErr, os.Setenv("GOFLAGS", previous))
		} else {
			resultErr = errors.Join(resultErr, os.Unsetenv("GOFLAGS"))
		}
	}()
	executable, err := os.Executable()
	if err != nil {
		return err
	}
	record, err := commandRun(work, []string{executable, "--instrument-producer", "normal"}, 2*time.Second)
	if err != nil || record.ExitCode != 0 || !bytes.Equal(record.Stdout, []byte("accepted-output")) || !bytes.Equal(record.Stderr, []byte("accepted-diagnostic")) {
		return errors.New("actual producer did not preserve independent expected streams")
	}
	if err = commandReaped(record); err != nil {
		return err
	}
	record, err = commandRun(work, []string{executable, "--instrument-producer", "environment"}, 2*time.Second)
	expectedEnvironment := "go1.26.10|0|off|linux|amd64|v1||"
	if err != nil || string(record.Stdout) != expectedEnvironment {
		return errors.New("actual producer lost a forced Go build environment boundary")
	}
	if err = commandReaped(record); err != nil {
		return err
	}
	marker := filepath.Join(work, "closed-stream-completed")
	record, err = commandRun(work, []string{executable, "--instrument-producer", "closed-streams"}, 2*time.Second)
	completed, readErr := os.ReadFile(marker) // #nosec G304 -- The fixed marker produced by the current private control child.
	if err != nil || record.ExitCode != 0 || readErr != nil || string(completed) != "completed" {
		return errors.New("closed streams terminated their still-running producer before its final write")
	}
	if err = commandReaped(record); err != nil {
		return err
	}
	for _, control := range []struct {
		mode, reason string
		deadline     time.Duration
	}{{"overflow", "output-limit", 2 * time.Second}, {"deadline", "deadline", 100 * time.Millisecond}, {"descendant", "deadline", 100 * time.Millisecond}} {
		started := time.Now()
		record, err = commandRun(work, []string{executable, "--instrument-producer", control.mode}, control.deadline)
		if time.Since(started) > control.deadline+1500*time.Millisecond {
			return errors.New("producer refusal exceeded its operation and cleanup time budget")
		}
		if control.mode == "overflow" && len(record.Stdout) != maxCommandOutput+1 {
			return errors.New("output refusal did not observe the exact oversized boundary")
		}
		if err == nil || record.Failure != control.reason {
			return errors.New("producer failure did not witness its intended property")
		}
		if err = commandReaped(record); err != nil {
			return err
		}
		if control.mode != "descendant" {
			continue
		}
		pid, err := strconv.Atoi(string(record.Stdout))
		if err != nil || pid <= 1 {
			return errors.New("descendant control did not identify its actual child")
		}
		deadline := time.Now().Add(2 * time.Second)
		for {
			body, err := os.ReadFile(filepath.Join("/proc", strconv.Itoa(pid), "stat")) // #nosec G304 -- The actual control producer's numeric child PID.
			if errors.Is(err, os.ErrNotExist) {
				break
			}
			if err != nil {
				return err
			}
			at := bytes.LastIndexByte(body, ')')
			if at < 0 {
				return errors.New("descendant state is malformed")
			}
			fields := strings.Fields(string(body[at+1:]))
			if len(fields) == 0 {
				return errors.New("descendant state is absent")
			}
			if fields[0] == "Z" || fields[0] == "X" {
				break
			}
			if time.Now().After(deadline) {
				return errors.New("private process group retained a live descendant")
			}
			time.Sleep(10 * time.Millisecond)
		}
	}
	return nil
}

func commandReaped(record commandRecord) error {
	if record.pid <= 1 {
		return errors.New("owned producer identity is absent")
	}
	var status syscall.WaitStatus
	_, err := syscall.Wait4(record.pid, &status, syscall.WNOHANG, nil)
	if !errors.Is(err, syscall.ECHILD) {
		return errors.New("owned direct producer was not reaped")
	}
	return nil
}
