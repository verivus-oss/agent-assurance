"""Exercise native history coverage against independently constructed Git graphs."""

import builtins
import errno
import hashlib
import os
from os.path import join
import zlib

import _credential_history as history
from _credential_git import GitProcess
from _credential_test_support import TemporaryTree, command, commit, initialize, write
from _temporary_attribute import temporary_attribute
from _test_require import expect_raises, require


def test_history_boundaries():
    with TemporaryTree() as outer:
        root = join(outer, "subject")
        os.mkdir(root)
        initialize(root)
        record = join(root, "credential.txt")
        write(record, b"public base\n")
        base = commit(root, "public base")
        pristine = history.scan_history(root)
        require(pristine["events"] == [] and pristine["head"] == base)
        command(root, "branch", "feature")
        write(record, b"public main\n")
        main = commit(root, "public main")
        command(root, "checkout", "-q", "feature")
        write(record, b"public feature\n")
        feature = commit(root, "public feature")
        command(root, "checkout", "-q", "main")
        result = command(root, "merge", "feature", allowed=(1,))
        require(result.returncode == 1 and command(root, "ls-files", "-u", "-z").stdout,
                "merge control failed to create a real conflict")
        planted = b"ghp_" + b"Ab12Cd34Ef56Gh78Ij90Kl12Mn34Op56Qr78"
        write(record, b"token=" + planted + b"\n")
        merge = commit(root, "resolve conflict with public unissued control")
        write(record, b"")
        deleted = commit(root, "deletion-only control")
        write(record, b"token=" + planted + b" # gitleaks:allow\n")
        inline = commit(root, "inline annotations cannot suppress candidates")
        os.mkdir(join(root, "renamed"))
        command(root, "mv", "credential.txt", "renamed/credential.txt")
        renamed = commit(root, "move credential to a new source identity")
        outside = join(outer, "outside.txt")
        write(outside, planted)
        os.symlink(outside, join(root, "link.txt"))
        linked = commit(root, "symlink target is a stored path, not an external file read")
        write(join(root, "untracked.txt"), planted)
        measured = history.scan_history(root)
        expected = {base, main, feature, merge, deleted, inline, renamed, linked}
        require(set(measured["commits"]) == expected)
        require(set(measured["scanned_commits"]) == expected)
        require(measured["head"] == linked and measured["scanned_blobs"])
        events = [event for event in measured["events"] if event["rule"] == "github-pat"]
        require({event["commit"] for event in events} == {merge, inline, renamed})
        require(all(event["capture_count"] == 1 and min(event["parent_capture_counts"]) == 0 for event in events))
        require(next(event for event in events if event["commit"] == merge)["parent_capture_counts"] == [0, 0])
        require(next(event for event in events if event["commit"] == renamed)["path"] == "renamed/credential.txt")
        require(not any(event.get("path") in ("untracked.txt", "link.txt") for event in measured["events"]))
        for event in events:
            for capture in event["captures"]:
                require(capture["source_sha256"] == event["source_sha256"])
                require(capture["value_sha256"] == hashlib.sha256(planted).hexdigest())
        # Replacement refs must not erase a stored historical candidate.
        command(root, "replace", merge, base)
        replaced = history.scan_history(root)
        require(replaced["events"] == measured["events"])
        command(root, "replace", "-d", merge)
        shallow = join(outer, "shallow")
        command(outer, "clone", "-q", "--depth", "1", "--no-local", "file://" + str(root), str(shallow))
        error = expect_raises(RuntimeError, lambda: history.scan_history(shallow), "shallow source was accepted")
        require("complete Git history" in str(error))
        grafts = join(root, ".git/info/grafts")
        write(grafts, (linked + "\n").encode())
        error = expect_raises(RuntimeError, lambda: history.scan_history(root), "grafted history was accepted")
        require("graft" in str(error))


def test_percent_candidates_with_invalid_neighbors():
    planted = b"ghp_" + b"Ab12Cd34Ef56Gh78Ij90Kl12Mn34Op56Qr78"
    encoded = b"".join(b"%" + format(byte, "02X").encode() for byte in planted)
    with TemporaryTree() as root:
        initialize(root)
        write(join(root, "public.txt"), b"public baseline\n")
        base = commit(root, "public baseline")
        expected = {}
        for name, data in (("prefix.txt", b"%00 " + encoded),
                           ("suffix.txt", encoded + b" %00"),
                           ("both.txt", b"%ff " + encoded + b" %08")):
            write(join(root, name), data)
            expected[name] = commit(root, "encoded candidate with an unrelated invalid escape")
        measured = history.scan_history(root)
        events = [event for event in measured["events"] if event["rule"] == "github-pat"]
        require({event["path"]: event["commit"] for event in events} == expected,
                "committed history omitted an encoded candidate beside an invalid escape")
        require(set(measured["scanned_commits"]) == {base, *expected.values()})
        for event in events:
            require(event["capture_count"] == 1 and min(event["parent_capture_counts"]) == 0)
            require(event["value_sha256"] == hashlib.sha256(planted).hexdigest())
            require(event["captures"][0]["decoding"]["kinds"] == ["percent"])


def test_missing_and_corrupt_subjects():
    with TemporaryTree() as root:
        expect_raises(RuntimeError, lambda: history.scan_history(root), "nonrepository subject passed")
        initialize(root)
        expect_raises(RuntimeError, lambda: history.scan_history(root), "absent HEAD passed")
        write(join(root, "public.txt"), b"public source")
        commit(root, "public source")
        fake = b"a" * 40
        object_directory = join(root, ".git/objects", fake[:2].decode())
        os.makedirs(object_directory, exist_ok=True)
        object_file = join(object_directory, fake[2:].decode())
        write(object_file, zlib.compress(b"blob 6\0wrong!"))
        with history.BlobReader(root) as reader:
            error = expect_raises(RuntimeError, lambda: reader.read(fake), "misnamed object bytes were trusted")
            require("do not match" in str(error), "corruption control did not reach content-identity verification")
        expect_raises(RuntimeError, lambda: list(history.tree_entries(b"")), "unframed tree response was accepted")
        for bad in (b"100644 blob short\tfile\0", b"100644 blob " + fake + b"\t\0",
                    b"100644 blob " + fake + b"\tfile\0" + b"100644 blob " + fake + b"\tfile\0"):
            expect_raises(RuntimeError, lambda: list(history.tree_entries(bad)), "malformed tree identity was accepted")


def test_object_formats_and_source_identity():
    for object_format in ("sha1", "sha256"):
        with TemporaryTree() as root:
            initialize(root, object_format)
            public = b"ghp_" + b"Ab12Cd34Ef56Gh78Ij90Kl12Mn34Op56Qr78"
            bad_path = os.fsencode(root) + b"/nonutf8-\xff.txt"
            write(bad_path, public)
            write(join(root, "empty.p12"), b"")
            base = commit(root, "byte-path and empty-file controls")
            command(root, "update-index", "--add", "--cacheinfo", "160000," + base + ",external")
            command(root, "commit", "-qm", "external repository reference control")
            head = command(root, "rev-parse", "HEAD").stdout.strip().decode()
            result = history.scan_history(root)
            require(result["head"] == head and set(result["commits"]) == {base, head})
            require(len(head) == (40 if object_format == "sha1" else 64))
            events = result["events"]
            require(len(events) == 2 and {event["commit"] for event in events} == {base})
            candidate = next(event for event in events if event["rule"] == "github-pat")
            require(candidate["path_bytes_hex"] == b"nonutf8-\xff.txt".hex() and "path" not in candidate)
            container = next(event for event in events if event["rule"] == "pkcs12-file")
            require(container["captures"][0]["kind"] == "file" and container["captures"][0]["byte_span"] == [0, 0])
            require(result["skips"]["external_gitlink_repositories"] == [{"path": "external", "target": base}])


def test_reference_movement():
    with TemporaryTree() as root:
        initialize(root)
        write(join(root, "public.txt"), b"public source")
        base = commit(root, "public source")
        original = history.git
        moved = []
        def update_reference(subject, arguments):
            result = original(subject, arguments)
            if arguments == ["rev-list", "HEAD"]:
                command(root, "update-ref", "refs/heads/new-reference", base)
                moved.append(True)
            return result
        history.git = update_reference
        try:
            error = expect_raises(RuntimeError, lambda: history.scan_history(root), "moving subject references were accepted")
            require(moved == [True] and "references moved" in str(error))
        finally:
            history.git = original


def test_transport_setup_failure_reaps_child_and_descriptors():
    modes = {"pipe", "errors", "spawn", "input", "output", "success"}
    visited = set()
    with TemporaryTree() as root:
        initialize(root)
        original_spawn, original_fdopen, original_pipe, original_open = os.posix_spawn, os.fdopen, os.pipe, builtins.open
        for mode in sorted(modes):
            children, descriptors, error_streams, pipe_calls = [], [], [], []
            marker = "controlled Git setup failure: " + mode

            def record_spawn(*arguments, selected_mode=mode, **options):
                if selected_mode == "spawn":
                    raise OSError(marker)
                pid = original_spawn(*arguments, **options)
                children.append(pid)
                return pid

            def record_pipe(selected_mode=mode):
                pipe_calls.append(True)
                if selected_mode == "pipe" and len(pipe_calls) == 2:
                    raise OSError(marker)
                pair = original_pipe()
                descriptors.extend(pair)
                return pair

            def record_errors(path, *arguments, selected_mode=mode, **options):
                if path == os.devnull and selected_mode == "errors":
                    raise OSError(marker)
                stream = original_open(path, *arguments, **options)
                if path == os.devnull:
                    error_streams.append(stream)
                return stream

            def open_stream(descriptor, access, selected_mode=mode):
                if (selected_mode, access) in (("input", "wb"), ("output", "rb")):
                    raise OSError(marker)
                return original_fdopen(descriptor, access)

            with temporary_attribute(os, "posix_spawn", record_spawn), temporary_attribute(os, "pipe", record_pipe), temporary_attribute(os, "fdopen", open_stream), temporary_attribute(builtins, "open", record_errors):
                if mode == "success":
                    process = GitProcess(root, ["status", "--porcelain"])
                    try:
                        process.stdin.close()
                        require(process.stdout.read() == b"" and process.wait() == 0)
                    finally:
                        process.close(failed=True)
                else:
                    error = expect_raises(OSError, lambda: GitProcess(root, ["status", "--porcelain"]), "setup failure passed")
                    require(str(error) == marker, "setup control failed for an unrelated reason")
            require(len(pipe_calls) == 2 and len(descriptors) == (2 if mode == "pipe" else 4))
            require(len(error_streams) == int(mode not in ("pipe", "errors")))
            require(all(stream.closed for stream in error_streams), "Git stderr descriptor leaked")
            require(len(children) == int(mode in ("input", "output", "success")))
            for child in children:
                expect_raises(ChildProcessError, lambda: os.waitpid(child, os.WNOHANG), "Git child was not reaped")
            for descriptor in descriptors:
                error = expect_raises(OSError, lambda: os.fstat(descriptor), "Git setup leaked a pipe descriptor")
                require(error.errno == errno.EBADF, "descriptor check failed for an unrelated reason")
            visited.add(mode)
    require(visited == modes, "transport setup control population did not execute")


if __name__ == "__main__":
    test_history_boundaries()
    test_percent_candidates_with_invalid_neighbors()
    test_missing_and_corrupt_subjects()
    test_object_formats_and_source_identity()
    test_reference_movement()
    test_transport_setup_failure_reaps_child_and_descriptors()
    print("native credential history: accepted graph and rejected coverage/integrity controls passed")
