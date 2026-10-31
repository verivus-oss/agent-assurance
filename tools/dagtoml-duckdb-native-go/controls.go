package main

import (
	"archive/tar"
	"archive/zip"
	"bytes"
	"compress/gzip"
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

func stampModule(root string) (resultErr error) {
	confined, err := os.OpenRoot(root)
	if err != nil {
		return err
	}
	defer func() { resultErr = errors.Join(resultErr, confined.Close()) }()
	const path = "src/duckdb_py/duckdb_python.cpp"
	data, err := confined.ReadFile(path)
	if err != nil {
		return err
	}
	const anchor = "PYBIND11_MODULE(DUCKDB_PYTHON_LIB_NAME, m) { // NOLINT"
	if strings.Count(string(data), anchor) != 1 {
		return errors.New("native module identity anchor differs")
	}
	const body = "\n\tm.attr(\"__dagtoml_binding_identity__\") = DAGTOML_BINDING_IDENTITY;\n"
	return confined.WriteFile(path, []byte(strings.Replace(string(data), anchor, anchor+body, 1)), 0600)
}

func instrumentProducer(mode string) error {
	switch mode {
	case "normal":
		_, outErr := os.Stdout.Write([]byte("accepted-output"))
		_, errorErr := os.Stderr.Write([]byte("accepted-diagnostic"))
		return errors.Join(outErr, errorErr)
	case "environment":
		_, err := fmt.Fprint(os.Stdout, strings.Join(os.Environ(), "\n"))
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
	previous, present := os.LookupEnv("CPLUS_INCLUDE_PATH")
	if err := os.Setenv("CPLUS_INCLUDE_PATH", "/untrusted/caller/header-override"); err != nil {
		return err
	}
	defer func() {
		if present {
			resultErr = errors.Join(resultErr, os.Setenv("CPLUS_INCLUDE_PATH", previous))
		} else {
			resultErr = errors.Join(resultErr, os.Unsetenv("CPLUS_INCLUDE_PATH"))
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
	expectedEnvironment := "PATH=/usr/bin:/bin\nLC_ALL=C\nTMPDIR=" + work + "\nSOURCE_DATE_EPOCH=0"
	if err != nil || string(record.Stdout) != expectedEnvironment || strings.Join(record.Environment, "\n") != expectedEnvironment {
		return errors.New("actual producer inherited an undeclared caller environment")
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

type archiveMember struct {
	name, body string
	link       bool
}

func tarControl(members []archiveMember, extra []byte) ([]byte, error) {
	var plain bytes.Buffer
	archive := tar.NewWriter(&plain)
	for _, member := range members {
		header := &tar.Header{Name: member.name, Mode: 0600, Size: int64(len(member.body)), Typeflag: tar.TypeReg}
		if member.link {
			header.Typeflag = tar.TypeSymlink
			header.Linkname = "outside"
			header.Size = 0
		}
		if err := archive.WriteHeader(header); err != nil {
			return nil, err
		}
		if !member.link {
			if _, err := archive.Write([]byte(member.body)); err != nil {
				return nil, err
			}
		}
	}
	if err := archive.Close(); err != nil {
		return nil, err
	}
	plain.Write(extra)
	var result bytes.Buffer
	compressed := gzip.NewWriter(&result)
	if _, err := compressed.Write(plain.Bytes()); err != nil {
		return nil, err
	}
	if err := compressed.Close(); err != nil {
		return nil, err
	}
	return result.Bytes(), nil
}

func zipControl(members []archiveMember) ([]byte, error) {
	var result bytes.Buffer
	archive := zip.NewWriter(&result)
	for _, member := range members {
		header := &zip.FileHeader{Name: member.name, Method: zip.Store}
		header.SetMode(0600)
		if member.link {
			header.SetMode(os.ModeSymlink | 0600)
		}
		writer, err := archive.CreateHeader(header)
		if err != nil {
			return nil, err
		}
		if _, err = writer.Write([]byte(member.body)); err != nil {
			return nil, err
		}
	}
	if err := archive.Close(); err != nil {
		return nil, err
	}
	return result.Bytes(), nil
}

func pybindControls(work string) error {
	item := headerInput{Version: "3.1.0"}
	header := archiveMember{"pybind11/include/pybind11/pybind11.h", "known header", false}
	license := archiveMember{"pybind11-3.1.0.dist-info/licenses/LICENSE", "known license", false}
	good, err := zipControl([]archiveMember{header, license})
	if err != nil {
		return err
	}
	accepted := filepath.Join(work, "accepted-pybind")
	if err = extractPybind(good, accepted, item); err != nil {
		return err
	}
	for path, expected := range map[string]string{"pybind11/pybind11.h": "known header", "LICENSE": "known license"} {
		body, err := os.ReadFile(filepath.Join(accepted, path))
		if err != nil || string(body) != expected {
			return errors.New("accepted header supplier content differs")
		}
	}
	for index, members := range [][]archiveMember{
		{header},
		{license},
		{header, {"pybind11-3.1.0.dist-info/LICENSE", "old layout", false}},
		{header, {"pybind11-3.0.0.dist-info/licenses/LICENSE", "other version", false}},
		{header, {"pybind11-3.1.0.dist-info/licenses/LICENSE", "", false}},
		{{"pybind11/include/pybind11/pybind11.h", "", false}, license},
	} {
		data, err := zipControl(members)
		if err != nil {
			return err
		}
		err = extractPybind(data, filepath.Join(work, "rejected-pybind-"+strconv.Itoa(index)), item)
		if err == nil || err.Error() != "header supplier license or entry point is absent or empty" {
			return errors.New("incomplete header supplier did not fail its intended admission property")
		}
	}
	return nil
}

func archiveControls(work string) error {
	if err := pybindControls(work); err != nil {
		return err
	}
	const selected = "duckdb-1.5.3/src/duckdb_py/control.cpp"
	item := versionInput{Version: "1.5.3"}
	good, err := tarControl([]archiveMember{{selected, "known-source", false}}, nil)
	if err != nil {
		return err
	}
	accepted := filepath.Join(work, "accepted-sdk")
	if err = extractSDK(good, accepted, item); err != nil {
		return err
	}
	actual, err := os.ReadFile(filepath.Join(accepted, "src/duckdb_py/control.cpp")) // #nosec G304 -- Fixed extracted control member.
	if err != nil || !bytes.Equal(actual, []byte("known-source")) {
		return errors.New("SDK positive control changed its expected source bytes")
	}
	cases := []struct {
		members []archiveMember
		reason  string
	}{
		{[]archiveMember{{"../outside", "bad", false}}, "SDK member is outside its declared version root"},
		{[]archiveMember{{"duckdb-1.5.3/../outside", "bad", false}}, "SDK member identity is invalid, repeated or exceeds its population bound"},
		{[]archiveMember{{selected, "one", false}, {selected, "two", false}}, "SDK member identity is invalid, repeated or exceeds its population bound"},
		{[]archiveMember{{selected, "", true}}, "SDK contains a linked or nonregular member"},
		{[]archiveMember{{"duckdb-1.5.3/ordinary.txt", "absent subject", false}}, "selected SDK source population is absent"},
	}
	for index, control := range cases {
		data, err := tarControl(control.members, nil)
		if err != nil {
			return err
		}
		if err = extractSDK(data, filepath.Join(work, "bad-sdk-"+strconv.Itoa(index)), item); err == nil || err.Error() != control.reason {
			return fmt.Errorf("SDK refusal did not witness its intended property: %v", err)
		}
	}
	trailer := append([]byte{}, good...)
	trailer[len(trailer)-1] ^= 1
	if err = extractSDK(trailer, filepath.Join(work, "bad-gzip"), item); err == nil || err.Error() != "SDK gzip trailer is invalid or exceeds its expansion/padding bound" {
		return fmt.Errorf("SDK checksum refusal did not witness its intended property: %v", err)
	}
	unaccounted, err := tarControl([]archiveMember{{selected, "known-source", false}}, []byte("unaccounted"))
	if err != nil {
		return err
	}
	if err = extractSDK(unaccounted, filepath.Join(work, "bad-tail"), item); err == nil || err.Error() != "SDK retains unaccounted data after its tar population" {
		return fmt.Errorf("SDK tail refusal did not witness its intended property: %v", err)
	}
	selectName := func(name string) (string, bool) { return "control.h", name == "include/control.h" }
	zipGood, err := zipControl([]archiveMember{{"include/control.h", "known-header", false}})
	if err != nil {
		return err
	}
	if err = extractZIP(zipGood, filepath.Join(work, "accepted-headers"), selectName); err != nil {
		return err
	}
	actual, err = os.ReadFile(filepath.Join(work, "accepted-headers/control.h")) // #nosec G304 -- Fixed extracted positive-control header.
	if err != nil || !bytes.Equal(actual, []byte("known-header")) {
		return errors.New("header positive control changed its expected bytes")
	}
	zipCases := []struct {
		members []archiveMember
		reason  string
	}{
		{[]archiveMember{{"../outside", "bad", false}}, "supplier ZIP identity is invalid, repeated or exceeds its bound"},
		{[]archiveMember{{"include/control.h", "one", false}, {"include/control.h", "two", false}}, "supplier ZIP identity is invalid, repeated or exceeds its bound"},
		{[]archiveMember{{"include/control.h", "outside", true}}, "supplier ZIP contains a linked or nonregular member"},
		{[]archiveMember{{"ordinary", "absent subject", false}}, "selected supplier ZIP population is absent"},
	}
	for index, control := range zipCases {
		data, err := zipControl(control.members)
		if err != nil {
			return err
		}
		if err = extractZIP(data, filepath.Join(work, "bad-zip-"+strconv.Itoa(index)), selectName); err == nil || err.Error() != control.reason {
			return fmt.Errorf("header refusal did not witness its intended property: %v", err)
		}
	}
	return nil
}

func controls() (resultErr error) {
	if _, err := loadInputs(); err != nil {
		return err
	}
	work, err := os.MkdirTemp("", "dagtoml-native-build-controls-")
	if err != nil {
		return err
	}
	defer func() { resultErr = errors.Join(resultErr, os.RemoveAll(work)) }()
	if err = processControls(work); err != nil {
		return err
	}
	if err = sourceControls(); err != nil {
		return err
	}
	if err = archiveControls(work); err != nil {
		return err
	}
	return nil
}
