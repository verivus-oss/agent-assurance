"""Byte captures for credential candidates, with explicit token and binding rules.

This is the detector being evaluated for the history gate. The active gate is
retired only after its full rule population has independent coverage evidence.
Candidates are review obligations, not claims that a service issued a value.
"""

import hashlib
from bisect import bisect_right

from _credential_primitives import (ALNUM, WORD, GENERIC, BASE64, Capture, FileCapture,
                                    all_bytes, bindings, entropy, occurrences, sensitive_name)


RULE_VERSION = "credential-candidates-v1"


def github_tokens(data):
    # These are fixed protocol prefixes and ASCII body requirements, not
    # runtime expressions or a user-configurable pattern language.
    kinds = ((b"ghp_", "github-pat", 36, ALNUM),
             (b"gho_", "github-oauth", 36, ALNUM),
             (b"ghu_", "github-app-token", 36, ALNUM),
             (b"ghs_", "github-app-token", 36, ALNUM),
             (b"ghr_", "github-refresh-token", 36, ALNUM),
             (b"github_pat_", "github-fine-grained-pat", 82, WORD))
    for prefix, rule, length, alphabet in kinds:
        for start in occurrences(data, prefix):
            end = start + len(prefix) + length
            if end <= len(data) and all_bytes(data[start + len(prefix):end], alphabet):
                if entropy(data[start:end]) >= 3:
                    yield Capture(rule, data, start, end)


def generic_tokens(data):
    from _credential_words import GENERIC_STOPWORDS
    for name, context_start, start, end in bindings(data):
        if not sensitive_name(name):
            continue
        value = data[start:end]
        word_value = 10 <= len(value) <= 150 and all_bytes(value, GENERIC)
        without_padding = value.rstrip(b"=")
        base64_value = (len(value) >= 12 and len(value) - len(without_padding) <= 3
                        and all_bytes(without_padding, BASE64))
        # Public identifiers and alphabet tables are not opaque credentials.
        # This preserves the generic detector's requirement for digit-bearing
        # candidates without suppressing known prefixed formats.
        if (word_value or base64_value) and any(byte in b"0123456789" for byte in value):
            if entropy(value) >= 3.5:
                if b"author" in data[context_start:end].lower() or any(word in value.lower() for word in GENERIC_STOPWORDS):
                    continue
                yield Capture("generic-api-key", data, start, end, context_start, end)


def scan_plain(data, path):
    captures = {}
    from _credential_formats import provider_bindings, provider_tokens
    from _credential_structures import structure_tokens, file_tokens
    for detector in (github_tokens, generic_tokens, provider_bindings, provider_tokens):
        for capture in detector(data):
            captures[(capture.rule, capture.start, capture.end)] = capture
    for capture in structure_tokens(data):
        captures[(capture.rule, capture.start, capture.end)] = capture
    for capture in file_tokens(data, path):
        captures[(capture.rule, capture.start, capture.end)] = capture
    provider_spans = sorted((capture.start, capture.end) for capture in captures.values()
                            if capture.rule != "generic-api-key")
    provider_starts, provider_ends = [], []
    longest = 0
    for start, end in provider_spans:
        provider_starts.append(start)
        longest = max(longest, end)
        provider_ends.append(longest)
    result = []
    for capture in captures.values():
        if capture.rule == "generic-api-key":
            index = bisect_right(provider_starts, capture.start) - 1
            if index >= 0 and capture.end <= provider_ends[index]:
                continue
        result.append(capture)
    return result


def scan_bytes(data, *, path=None, decode_depth=5):
    if not isinstance(data, bytes):
        raise TypeError("credential detection requires the original source bytes")
    if type(decode_depth) is not int or not 0 <= decode_depth <= 5:
        raise ValueError("credential decoding requires a depth from zero through five")
    from _credential_decoding import VERSION, View
    source_digest = hashlib.sha256(data).hexdigest()
    view, captures = View(data), {}
    for depth in range(decode_depth + 1):
        derived_digest = None
        for capture in scan_plain(view.data, path):
            if isinstance(capture, FileCapture):
                if depth:
                    continue
            elif depth:
                value_start, value_end = capture.start, capture.end
                capture.start, capture.end, kinds = view.source_span(value_start, value_end)
                capture.context_start, capture.context_end, context_kinds = view.source_span(capture.context_start, capture.context_end)
                kinds = tuple(sorted(set(kinds) | set(context_kinds)))
                if kinds:
                    if derived_digest is None:
                        derived_digest = hashlib.sha256(view.data).hexdigest()
                    capture.decoding = {"version": VERSION, "depth": depth, "kinds": list(kinds),
                                        "derived_source_sha256": derived_digest,
                                        "derived_byte_span": [value_start, value_end]}
            capture.source_sha256 = source_digest
            key = (capture.rule, capture.start, capture.end, capture.value_sha256)
            if key not in captures:
                captures[key] = capture
        if depth == decode_depth:
            break
        view = view.decode()
        if view is None:
            break
    return tuple(captures[key] for key in sorted(captures))
