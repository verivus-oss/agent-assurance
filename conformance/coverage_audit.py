#!/usr/bin/env python3
"""Mutation-based coverage audit of the profile kind-layer validators.

Every `errors.append(...)` in a reference validator IS a check. This disables
each one individually, runs the repository's own gates, and restores the file.
A check whose removal nothing notices is a check nothing tests, even when the
code is correct.

WHY THIS EXISTS

Three independent cross-model review rounds each found a different untested
check in this surface, by guessing well. That is evidence that guessing is not
a reliable way to find the rest: the first audit run showed 25 unprotected
checks where reviewers had found 4.

The cause is one construction defect, not 25 oversights. The corpus was built
by taking a known-good document and mutating a single field, so every fixture
inherits correct values everywhere else. Any check on a field the fixtures all
get right is structurally invisible to the oracle.

DETECTION IS BASELINE-RELATIVE, AND THAT MATTERS

An earlier version of this audit called a mutation "detected" whenever any
`examples/negative/` fixture was accepted by the validator under test. That was
wrong: several of those fixtures are closure-layer negatives which the kind
validator never rejected, so the rule fired on a pre-existing condition and
reported 28 of 28 caught. A uniform result is what exposed it.

So detection is measured against a baseline recorded before any mutation:
a mutation is DETECTED only when something that was rejected before becomes
accepted after, or a suite that passed now fails.

USAGE
    python3 conformance/coverage_audit.py --rs <rs-binary> --go <go-binary>
        [--repo-root .] [--baseline conformance/coverage-baseline.toml]

Exit 0 when the number of unprotected checks is at or below the declared
baseline, 1 when it regresses above it, 2 on an infrastructure error.
"""

from __future__ import annotations

import argparse
import ast
import atexit
import re
import os
import pathlib
import signal
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "validators"))
import _toml11 as tomllib  # noqa: E402

# validator -> the examples/negative glob whose rejections form its baseline.
AUDITED = {
    "validators/validate_api_snapshot.py": "examples/negative/api-snapshot-*.toml",
    "validators/validate_state_mutation.py": "examples/negative/state-mutation-*.toml",
}

# Fixtures excluded from the baseline: their defect makes the kind validator
# decline to run at all, so they carry no signal about individual checks.
BASELINE_SKIP = ("malformed-kind-selector",)


class DisableSite(ast.NodeTransformer):
    """Replace the Nth errors/defects `.append(...)` statement with `pass`."""

    def __init__(self, target: int) -> None:
        self.target = target
        self.seen = 0
        self.line: int | None = None
        self.fingerprint: str = ""

    def visit_Expr(self, node: ast.Expr):
        call = node.value
        if (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "append"
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id in ("errors", "defects")
        ):
            index = self.seen
            self.seen += 1
            if index == self.target:
                self.line = node.lineno
                self.fingerprint = fingerprint(call)
                return ast.copy_location(ast.Pass(), node)
        return node


def fingerprint(call: ast.Call) -> str:
    """A stable identity for a check, derived from its message rather than its line.

    Line numbers move whenever anything above them is edited, so a baseline keyed
    on them would churn on unrelated changes and, worse, could be silently
    re-pointed at a different check. The message text is what actually identifies
    the rule.
    """
    parts: list[str] = []
    for node in ast.walk(call):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            parts.append(node.value)
    text = " ".join(parts)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:70] if text else "<no-literal>"


def run(cmd: list[str], root: pathlib.Path) -> int:
    return subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=900).returncode


class Restorer:
    """Guarantee the audited file is put back, including on SIGTERM/SIGINT.

    A `try/finally` is NOT sufficient here and that is not theoretical: this
    audit was once killed by an outer timeout partway through a mutation, the
    finally never ran, and it left a validator as bare `ast.unparse` output with
    its shebang, comments and 271 lines gone. A tool that rewrites source files
    in place must survive being killed, or it is a hazard to the tree it audits.

    So the original bytes are held here, restored on normal exit via the context
    manager, on fatal signals via a handler, and on interpreter shutdown via
    atexit. Restoring twice is harmless; restoring zero times is not.
    """

    def __init__(self, path: pathlib.Path) -> None:
        self.path = path
        self.original = path.read_text()
        self._armed = False

    def _restore(self, *_args) -> None:
        if self._armed:
            self.path.write_text(self.original)

    def __enter__(self) -> "Restorer":
        self._armed = True
        atexit.register(self._restore)
        self._prev = {
            sig: signal.signal(sig, self._on_signal)
            for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)
            if hasattr(signal, sig.name)
        }
        return self

    def _on_signal(self, signum, frame):
        self._restore()
        # Re-raise with the default disposition so the caller still sees the kill.
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)

    def __exit__(self, *exc) -> None:
        self._restore()
        self._armed = False
        for sig, prev in getattr(self, "_prev", {}).items():
            signal.signal(sig, prev)
        atexit.unregister(self._restore)


def rejected(validator: str, pattern: str, root: pathlib.Path) -> set[str]:
    out: set[str] = set()
    for f in sorted(root.glob(pattern)):
        rel = str(f.relative_to(root))
        if any(s in rel for s in BASELINE_SKIP):
            continue
        if run([sys.executable, validator, "--repo-root", ".", rel], root) != 0:
            out.add(rel)
    return out


def suites_pass(root: pathlib.Path, rs: str, go: str) -> bool:
    if run([sys.executable, "conformance/runner.py", "--rs", rs, "--go", go], root) != 0:
        return False
    return run(
        [sys.executable, "validators/validate_closure_root.py", "--discover", ".",
         "--exclude", "examples/negative"], root
    ) == 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--rs", required=True)
    ap.add_argument("--go", required=True)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--baseline", default="conformance/coverage-baseline.toml")
    args = ap.parse_args()
    root = pathlib.Path(args.repo_root).resolve()

    baseline_doc = tomllib.loads((root / args.baseline).read_text())
    allowed = int(baseline_doc["coverage"]["max_unprotected_checks"])

    base_rejects = {v: rejected(v, p, root) for v, p in AUDITED.items()}
    if not suites_pass(root, args.rs, args.go):
        print("error: baseline suites do not pass; fix the tree before auditing", file=sys.stderr)
        return 2

    unprotected: list[tuple[str, int, str]] = []
    audited = 0
    for validator, pattern in AUDITED.items():
        path = root / validator
        with Restorer(path) as keeper:
            original = keeper.original
            probe = DisableSite(-1)
            probe.visit(ast.parse(original))
            for i in range(probe.seen):
                tr = DisableSite(i)
                tree = tr.visit(ast.parse(original))
                ast.fix_missing_locations(tree)
                path.write_text(ast.unparse(tree))
                try:
                    lost = base_rejects[validator] - rejected(validator, pattern, root)
                    detected = bool(lost) or not suites_pass(root, args.rs, args.go)
                finally:
                    path.write_text(original)
                audited += 1
                if not detected:
                    unprotected.append((validator, tr.line or 0, tr.fingerprint))

    declared = set(baseline_doc["coverage"].get("unprotected", []))
    actual = {f"{v}|{fp}" for v, _line, fp in unprotected}

    print("COVERAGE AUDIT")
    print(f"- checks audited      : {audited}")
    print(f"- unprotected         : {len(unprotected)}")
    print(f"- declared baseline   : {allowed}")
    for validator, line, fp in sorted(unprotected):
        print(f"  UNPROTECTED {validator}:{line}  {fp}")

    # The SET matters, not only the count. A count-only ratchet is fungible:
    # closing an easy check while opening a hard one leaves the number identical
    # and the gate green. Comparing identities makes that swap a visible failure.
    appeared = sorted(actual - declared)
    if appeared:
        print("\nFAIL: checks that are newly unprotected and not in the declared baseline:",
              file=sys.stderr)
        for item in appeared:
            print(f"  {item}", file=sys.stderr)
        print(
            f"\nAdd a fixture that exercises each, or record it DELIBERATELY in "
            f"{args.baseline} with a reason. Swapping one unprotected check for another "
            f"is exactly what this comparison exists to catch.",
            file=sys.stderr,
        )
        return 1
    if len(unprotected) > allowed:
        print(f"\nFAIL: {len(unprotected)} exceeds the declared baseline of {allowed}.",
              file=sys.stderr)
        return 1
    closed = sorted(declared - actual)
    if closed:
        print(f"\nNOTE: {len(closed)} check(s) newly protected. Ratchet {args.baseline} "
              f"down and remove them from `unprotected` to lock the improvement in:")
        for item in closed:
            print(f"  {item}")
    print("\nCOVERAGE AUDIT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
