package main

import (
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
)

func publishedPopulation(root, expected string, count int) error {
	metadata, err := os.Lstat(root)
	if err != nil || !metadata.IsDir() || metadata.Mode()&os.ModeSymlink != 0 {
		return errors.New("published supplier root is absent or not a regular directory")
	}
	files, _, err := population(root)
	if err != nil || len(files) != count || dependencyInventory(files) != expected {
		return errors.New("published supplier population differs from its prepared identity")
	}
	return nil
}

func publishDependencies(output string, files []sourceFile, expected string) (resultErr error) {
	if len(files) == 0 || dependencyInventory(files) != expected {
		return errors.New("supplier publication has no complete prepared population")
	}
	seen := map[string]bool{}
	for _, file := range files {
		digest := sha256.Sum256(file.Data)
		if !fs.ValidPath(file.Path) || file.Path == "." || strings.ContainsAny(file.Path, "\\\x00\r\n\t") || seen[file.Path] || hex.EncodeToString(digest[:]) != file.SHA256 {
			return errors.New("supplier publication input is invalid, repeated or changed")
		}
		seen[file.Path] = true
	}
	parent := output + ".dependencies"
	if err := os.MkdirAll(parent, 0700); err != nil {
		return err
	}
	metadata, err := os.Lstat(parent)
	if err != nil || !metadata.IsDir() || metadata.Mode()&os.ModeSymlink != 0 {
		return errors.New("supplier publication parent is not a regular directory")
	}
	destination := filepath.Join(parent, expected)
	if _, err := os.Lstat(destination); err == nil {
		return publishedPopulation(destination, expected, len(files))
	} else if !errors.Is(err, fs.ErrNotExist) {
		return err
	}
	work, err := os.MkdirTemp(parent, ".prepared-")
	if err != nil {
		return err
	}
	defer func() { resultErr = errors.Join(resultErr, os.RemoveAll(work)) }()
	confined, err := os.OpenRoot(work)
	if err != nil {
		return err
	}
	defer func() { resultErr = errors.Join(resultErr, confined.Close()) }()
	for _, file := range files {
		path := filepath.FromSlash(file.Path)
		if err = confined.MkdirAll(filepath.Dir(path), 0700); err != nil {
			return err
		}
		if err = confined.WriteFile(path, file.Data, 0600); err != nil {
			return err
		}
	}
	if err = publishedPopulation(work, expected, len(files)); err != nil {
		return err
	}
	if err = os.Rename(work, destination); err != nil {
		// A concurrent build may have published the identical immutable tree.
		return publishedPopulation(destination, expected, len(files))
	}
	return nil
}

func publicationControls() (resultErr error) {
	work, err := os.MkdirTemp("", "dagtoml-supplier-publication-")
	if err != nil {
		return err
	}
	defer func() { resultErr = errors.Join(resultErr, os.RemoveAll(work)) }()
	file := func(path, body string) sourceFile {
		data := []byte(body)
		sum := sha256.Sum256(data)
		return sourceFile{Path: path, Data: data, SHA256: hex.EncodeToString(sum[:])}
	}
	files := []sourceFile{file("module/LICENSE", "known-notice"), file("module/main.go", "package fixture\n")}
	stamp := dependencyInventory(files)
	output := filepath.Join(work, "producer")
	if err = publishDependencies(output, files, stamp); err != nil {
		return err
	}
	root := output + ".dependencies/" + stamp
	for name, expected := range map[string]string{"module/LICENSE": "known-notice", "module/main.go": "package fixture\n"} {
		data, err := os.ReadFile(filepath.Join(root, name)) // #nosec G304 -- Fixed positive-control source names in the just-published private tree.
		if err != nil || string(data) != expected {
			return errors.New("published supplier bytes differ from independent expected values")
		}
	}
	if err = publishDependencies(output, files, stamp); err != nil {
		return err
	}
	notice := filepath.Join(root, "module/LICENSE")
	if err = os.WriteFile(notice, []byte("changed-notice"), 0600); err != nil {
		return err
	}
	if err = publishDependencies(output, files, stamp); err == nil || err.Error() != "published supplier population differs from its prepared identity" {
		return errors.New("changed supplier notice did not witness publication refusal")
	}
	if err = os.Remove(notice); err != nil {
		return err
	}
	if err = publishedPopulation(root, stamp, len(files)); err == nil || err.Error() != "published supplier population differs from its prepared identity" {
		return errors.New("missing supplier notice did not witness publication refusal")
	}
	if err = os.WriteFile(notice, []byte("known-notice"), 0600); err != nil {
		return err
	}
	extra := filepath.Join(root, "unexpected")
	if err = os.WriteFile(extra, []byte("unexpected source"), 0600); err != nil {
		return err
	}
	if err = publishedPopulation(root, stamp, len(files)); err == nil || err.Error() != "published supplier population differs from its prepared identity" {
		return errors.New("extra supplier member did not witness publication refusal")
	}
	if err = os.Remove(extra); err != nil {
		return err
	}
	if err = publishedPopulation(root, stamp, len(files)); err != nil {
		return err
	}
	for _, invalid := range [][]sourceFile{nil, {files[0], files[0]}, {file("../outside", "source")}, {{Path: "module/changed", SHA256: strings.Repeat("0", 64), Data: []byte("source")}}} {
		err = publishDependencies(filepath.Join(work, "invalid"), invalid, dependencyInventory(invalid))
		if err == nil || (err.Error() != "supplier publication has no complete prepared population" && err.Error() != "supplier publication input is invalid, repeated or changed") {
			return errors.New("invalid supplier input did not witness its intended refusal")
		}
	}
	return nil
}
