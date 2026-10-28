"""Audit stored Git blobs in complete parent-first reachable history."""

import hashlib
import os

from _credential_detection import RULE_VERSION, scan_bytes
from _credential_git import GitProcess, git


def object_id(value):
    return len(value) in (40, 64) and not value.translate(None, b"0123456789abcdef")


def tree_entries(output):
    if not output.endswith(b"\0"):
        raise RuntimeError("Git tree did not have complete byte framing")
    seen = set()
    for record in output.split(b"\0")[:-1]:
        header, separator, path = record.partition(b"\t")
        fields = header.split(b" ")
        if (not separator or not path or path in seen or len(fields) != 3
                or not object_id(fields[2])):
            raise RuntimeError("Git tree contained an invalid or duplicate source identity")
        mode, kind, sha = fields
        if (mode, kind) not in ((b"100644", b"blob"), (b"100755", b"blob"),
                                (b"120000", b"blob"), (b"160000", b"commit")):
            raise RuntimeError("Git tree contained an unsupported entry kind")
        seen.add(path)
        yield kind, sha, path


class BlobReader:
    def __init__(self, root):
        self.process = GitProcess(root, ["cat-file", "--batch"])

    def __enter__(self):
        return self

    def __exit__(self, error_type, *_error):
        self.process.close(failed=error_type is not None)
        if error_type is None and self.process.status:
            raise RuntimeError("Git object reader did not exit successfully")

    def read(self, sha):
        if not object_id(sha):
            raise RuntimeError("invalid requested Git blob identity")
        self.process.stdin.write(sha + b"\n")
        self.process.stdin.flush()
        header = self.process.stdout.readline().removesuffix(b"\n").split(b" ")
        if len(header) != 3 or header[0] != sha or header[1] != b"blob" or not header[2].isdigit():
            raise RuntimeError("Git object reader did not return the requested blob")
        size = int(header[2])
        content = self.process.stdout.read(size)
        if len(content) != size or self.process.stdout.read(1) != b"\n":
            raise RuntimeError("Git object reader returned truncated blob bytes")
        framed = b"blob " + str(size).encode("ascii") + b"\0" + content
        digest = (hashlib.sha1(framed, usedforsecurity=False).hexdigest() if len(sha) == 40
                  else hashlib.sha256(framed).hexdigest())
        if digest.encode("ascii") != sha:
            raise RuntimeError("Git object bytes do not match the requested content identity")
        return content


def path_record(path):
    try:
        return {"path": path.decode("utf-8")}
    except UnicodeDecodeError:
        return {"path_bytes_hex": path.hex()}


def scan_history(root):
    root = os.path.realpath(root)
    actual = git(root, ["rev-parse", "--show-toplevel"]).removesuffix(b"\n")
    if os.path.realpath(os.fsdecode(actual)) != root:
        raise RuntimeError("credential history root must be the repository root")
    if git(root, ["rev-parse", "--is-shallow-repository"]).strip() != b"false":
        raise RuntimeError("credential scan requires complete Git history")
    graft_path = os.fsdecode(git(root, ["rev-parse", "--git-path", "info/grafts"]).removesuffix(b"\n"))
    graft_path = graft_path if os.path.isabs(graft_path) else os.path.join(root, graft_path)
    if os.path.exists(graft_path):
        with open(graft_path, "rb") as source:
            if source.read().strip():
                raise RuntimeError("credential scan refuses rewritten graft history")
    head = git(root, ["rev-parse", "HEAD"]).strip()
    if not object_id(head):
        raise RuntimeError("credential history has no named HEAD")
    reference_population = git(root, ["for-each-ref", "--format=%(refname)%00%(objectname)%00"])
    commits = []
    for record in git(root, ["rev-list", "--topo-order", "--reverse", "--parents", "--all", "HEAD"]).splitlines():
        fields = record.split(b" ")
        if not fields or any(not object_id(item) for item in fields):
            raise RuntimeError("Git returned an invalid history population")
        commits.append((fields[0], tuple(fields[1:])))
    required = {sha for sha, _ in commits}
    if not required or len(required) != len(commits) or head not in required:
        raise RuntimeError("Git did not return a complete distinct HEAD population")
    states, scanned, cache, blobs, events, links = {}, set(), {}, set(), [], set()
    head_blobs = set()
    with BlobReader(root) as reader:
        for sha, parents in commits:
            if any(parent not in states for parent in parents):
                raise RuntimeError("credential history is not complete and parent-first")
            current = {}
            output = git(root, ["ls-tree", "-r", "-z", "--full-tree", sha.decode("ascii")])
            if output:
                entries = tree_entries(output)
            else:
                entries = ()
            for kind, blob, path in entries:
                if kind == b"commit":
                    links.add((path, blob))
                    continue
                blobs.add(blob)
                if sha == head:
                    head_blobs.add(blob)
                key = blob, path
                if key not in cache:
                    data = reader.read(blob)
                    captures = scan_bytes(data, path=path)
                    grouped = {}
                    for capture in captures:
                        identity = capture.rule, capture.value_sha256
                        grouped.setdefault(identity, []).append(capture.record())
                    cache[key] = grouped, hashlib.sha256(data).hexdigest()
                groups, source_digest = cache[key]
                for (rule, value_digest), records in groups.items():
                    identity = path, rule, value_digest
                    current[identity] = len(records)
                    previous = [states[parent].get(identity, 0) for parent in parents] or [0]
                    if len(records) > min(previous):
                        events.append({"commit": sha.decode("ascii"), **path_record(path),
                                       "blob": blob.decode("ascii"), "source_sha256": source_digest,
                                       "rule": rule, "value_sha256": value_digest,
                                       "capture_count": len(records), "parent_capture_counts": previous,
                                       "captures": records})
            states[sha] = current
            scanned.add(sha)
    if scanned != required or not blobs or not head_blobs:
        raise RuntimeError("credential scan did not cover a nonempty complete HEAD history")
    ancestry = set(git(root, ["rev-list", "HEAD"]).splitlines())
    if not ancestry or not ancestry <= required:
        raise RuntimeError("credential scan did not establish its HEAD ancestry")
    if (git(root, ["rev-parse", "HEAD"]).strip() != head
            or git(root, ["for-each-ref", "--format=%(refname)%00%(objectname)%00"]) != reference_population):
        raise RuntimeError("credential scan subject references moved during traversal")
    return {"schema_version": "credential-history-v1", "detector_version": RULE_VERSION,
            "reference_population_sha256": hashlib.sha256(reference_population).hexdigest(),
            "head": head.decode("ascii"), "commits": sorted(sha.decode("ascii") for sha in required),
            "head_ancestry": sorted(sha.decode("ascii") for sha in ancestry),
            "scanned_commits": sorted(sha.decode("ascii") for sha in scanned),
            "scanned_blobs": sorted(blob.decode("ascii") for blob in blobs),
            "events": events,
            "skips": {"external_gitlink_repositories": [dict(path_record(path), target=target.decode("ascii"))
                                                       for path, target in sorted(links)],
                      "compressed_members": "stored blob bytes are scanned without expanding archive members"}}
