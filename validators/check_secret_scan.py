#!/usr/bin/env python3
"""Check native byte candidates in complete committed Git history."""

import os
import sys

from _credential_history import object_id, scan_history
from _credential_report import encode_report


PUBLIC_HEX_SHA256 = "9f9f5111f7b27a781f1f1ddde5ebc2dd2b796bfc7365c9c28b548e564176929f"
PUBLIC_HEX_FILE = "validators/unresolvable-commit-citations.toml"
PUBLIC_HEX_RULE = "generic-api-key"
KNOWN_COMMITS = frozenset({
    "6c0b27b19d2cbaf32ddaaff2638175f18d683974",
    "f64bfa0500802eee910e27f40c6d4152474c2252",
    "8e52e9bab66d4e2bc1b52b427f69ef0c562096ff",
    "ffac3a202344f42f7608795866065971a08d42ed",
})


def known_public_literal(event):
    return (
        event.get("rule") == PUBLIC_HEX_RULE
        and event.get("path") == PUBLIC_HEX_FILE
        and event.get("commit") in KNOWN_COMMITS
        and event.get("value_sha256") == PUBLIC_HEX_SHA256
        and event.get("capture_count") == 1
        and type(event.get("capture_count")) is int
        and isinstance(event.get("parent_capture_counts"), list)
        and bool(event["parent_capture_counts"])
        and all(type(count) is int and count >= 0 for count in event["parent_capture_counts"])
        and min(event["parent_capture_counts"]) == 0
        and isinstance(event.get("captures"), list)
        and len(event["captures"]) == 1
        and isinstance(event["captures"][0], dict)
        and "decoding" not in event["captures"][0]
        and event["captures"][0].get("rule") == PUBLIC_HEX_RULE
        and event["captures"][0].get("value_sha256") == PUBLIC_HEX_SHA256
        and event["captures"][0].get("source_sha256") == event.get("source_sha256")
        and isinstance(event.get("source_sha256"), str)
        and len(event["source_sha256"]) == 64
        and object_id(event["source_sha256"].encode("utf-8"))
    )


def check_findings(events, expected):
    seen = set()
    unexpected = []
    for event in events:
        if not isinstance(event, dict) or not known_public_literal(event):
            unexpected.append(event)
            continue
        commit = event["commit"]
        if commit in seen:
            raise RuntimeError("credential scan repeated a known public event")
        seen.add(commit)
    if unexpected:
        print("FAIL: credential scan reported " + str(len(unexpected)) + " unapproved event(s)", file=sys.stderr)
        for event in unexpected:
            if isinstance(event, dict):
                print("  rule=" + repr(event.get("rule")) + " path=" + repr(event.get("path", event.get("path_bytes_hex")))
                      + " commit=" + repr(event.get("commit")), file=sys.stderr)
        raise RuntimeError("credential scan found candidates for review")
    if seen != expected:
        raise RuntimeError("known public event population changed; review the scan and exception")


def commit_set(values):
    if (not isinstance(values, list) or not values or any(not isinstance(item, str)
            or not object_id(item.encode("utf-8")) for item in values) or len(set(values)) != len(values)):
        raise RuntimeError("credential scan did not return a distinct named commit population")
    return set(values)


def check_scan_population(result):
    reachable = commit_set(result["commits"])
    scanned = commit_set(result["scanned_commits"])
    ancestry = commit_set(result["head_ancestry"])
    blobs = commit_set(result["scanned_blobs"])
    if scanned != reachable or not ancestry <= reachable or result["head"] not in ancestry or not blobs:
        raise RuntimeError("credential scan coverage disagrees with the declared Git population")
    expected = KNOWN_COMMITS & reachable
    if not expected or not (expected & ancestry):
        raise RuntimeError("known public finding control is absent from HEAD ancestry")
    return expected


def main():
    options = {"--repo-root": ".", "--report": None}
    seen = set()
    arguments = iter(sys.argv[1:])
    for argument in arguments:
        if argument in ("--help", "-h"):
            print("usage: check_secret_scan.py [--repo-root PATH] [--report PATH]")
            return
        name, separator, value = argument.partition("=")
        if name not in options or name in seen:
            raise RuntimeError("unknown or repeated credential scan option: " + name)
        value = value if separator else next(arguments, "")
        if not value or value.startswith("--"):
            raise RuntimeError("credential scan option requires a path: " + name)
        options[name] = value
        seen.add(name)
    result = scan_history(os.path.realpath(options["--repo-root"]))
    expected = check_scan_population(result)
    # Reports contain immutable source identities, digests and byte spans,
    # never credential plaintext or stored source coordinates.
    if options["--report"]:
        with open(options["--report"], "w", encoding="utf-8") as report:
            report.write(encode_report(result) + "\n")
    check_findings(result["events"], expected)
    print("credential scan at " + result["head"] + ": complete reachable commit and stored blob sets compared; "
          + "exact historical public events checked, no unapproved events")
    print("scope: committed blob bytes only; untracked and uncommitted files, external gitlink repositories "
          + "and expanded archive members are outside this scan")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, TypeError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
