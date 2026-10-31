package main

import "errors"

func capsuleControls() error {
	const manifest = "module example.invalid/producer\n\ngo 1.26.10\n"
	accepted := []sourceFile{{Path: "go.mod", Data: []byte(manifest)}, {Path: "main.go", Data: []byte("package main\nimport \"net/http\"\nfunc main(){_ = http.MethodGet}\n")}}
	module, err := capsuleModule(accepted)
	if err != nil || module != "example.invalid/producer" {
		return errors.New("standard-library command was refused")
	}
	for _, directive := range []string{"require other.invalid/module v1.0.0", "replace other.invalid/module => ../other", "toolchain go1.26.10", "go 1.26.10", "module example.invalid/second", "unknown value"} {
		files := append([]sourceFile{}, accepted...)
		files[0].Data = []byte(manifest + directive + "\n")
		if _, err := capsuleModule(files); err == nil {
			return errors.New("unsupported module directive was admitted")
		}
	}
	for _, imported := range []string{"regexp", "regexp/syntax", "unsafe"} {
		files := append([]sourceFile{}, accepted...)
		files[1].Data = []byte("package main\nimport _ \"" + imported + "\"\nfunc main(){}\n")
		if _, err := capsuleModule(files); err == nil {
			return errors.New("unsupported import was admitted")
		}
	}
	for _, suffix := range []string{".s", ".S", ".c", ".h", ".cc", ".cpp", ".syso"} {
		files := append(append([]sourceFile{}, accepted...), sourceFile{Path: "extra" + suffix, Data: []byte("uncompiled input")})
		if _, err := capsuleModule(files); err == nil {
			return errors.New("native source was admitted")
		}
	}
	for _, pin := range []string{"1.26", "1.26.9", "1.27.0", ""} {
		files := append([]sourceFile{}, accepted...)
		files[0].Data = []byte("module example.invalid/producer\ngo " + pin + "\n")
		if _, err := capsuleModule(files); err == nil {
			return errors.New("unsupported Go pin was admitted")
		}
	}
	return nil
}
