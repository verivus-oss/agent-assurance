"""Byte captures for credential candidates, with explicit token and binding rules.

This is the detector being evaluated for the history gate. The active gate is
retired only after its full rule population has independent coverage evidence.
Candidates are review obligations, not claims that a service issued a value.
"""

import hashlib
import math
from bisect import bisect_right


ALNUM = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
WORD = ALNUM + b"_"
IDENTIFIER = WORD + b".-"
GENERIC = WORD + b".=-"
BASE64 = ALNUM + b"+/"
VALUE = GENERIC + b"+/"
SPACE = b" \t\r\n\v\f"
RULE_VERSION = "credential-candidates-v1"


class Capture:
    __slots__ = ("rule", "start", "end", "context_start", "context_end", "value_sha256", "source_sha256", "decoding")

    def __init__(self, rule, data, start, end, context_start=None, context_end=None):
        context_start = start if context_start is None else context_start
        context_end = end if context_end is None else context_end
        if not 0 <= context_start <= start < end <= context_end <= len(data):
            raise ValueError("credential capture must identify a nonempty byte span inside its context")
        self.rule = rule
        self.start = start
        self.end = end
        self.context_start = context_start
        self.context_end = context_end
        self.value_sha256 = hashlib.sha256(data[start:end]).hexdigest()
        self.source_sha256 = None
        self.decoding = None

    def record(self):
        if self.source_sha256 is None:
            raise ValueError("serialize source-bound captures returned by scan_bytes")
        result = {"rule": self.rule, "byte_span": [self.start, self.end],
                  "context_byte_span": [self.context_start, self.context_end],
                  "value_sha256": self.value_sha256, "source_sha256": self.source_sha256}
        if self.decoding is not None:
            result["decoding"] = self.decoding
        return result


class FileCapture(Capture):
    """A file-kind obligation, including a legitimately empty file object."""

    def __init__(self, rule, data):
        self.rule = rule
        self.start = self.context_start = 0
        self.end = self.context_end = len(data)
        self.value_sha256 = hashlib.sha256(data).hexdigest()
        self.source_sha256 = self.value_sha256
        self.decoding = None

    def record(self):
        return {"rule": self.rule, "kind": "file", "byte_span": [self.start, self.end],
                "source_sha256": self.value_sha256}


def all_bytes(value, alphabet):
    return bool(value) and not value.translate(None, alphabet)


def entropy(value):
    if not value:
        return 0.0
    counts = [0] * 256
    for byte in value:
        counts[byte] += 1
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts if count)


def occurrences(data, value):
    position = data.find(value)
    while position != -1:
        yield position
        position = data.find(value, position + 1)


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


def sensitive_name(name):
    name = name.lower()
    compact = name.replace(b"_", b"").replace(b"-", b"").replace(b".", b"")
    markers = {marker for marker in (b"access", b"auth", b"api", b"credential", b"creds",
                                     b"key", b"passwd", b"password", b"secret", b"token")
               if marker in name}
    if not markers:
        return False
    # Identify metadata operands rather than blanket-exempting a source file
    # or a candidate's value. Prefixed-token checks remain independent.
    metadata = (b"accessid", b"apiid", b"apiname", b"apiversion", b"credentialid", b"credentialsid",
                b"keyalias", b"keycode", b"keyframe", b"keyid", b"keylength", b"keyname", b"keypair",
                b"keypressed", b"keyring", b"keyselector", b"keysignature", b"keysize", b"keystoretype",
                b"keyvaultid", b"keyvaultname", b"keystorefile", b"keystorepath", b"keytabfile",
                b"keytabpath", b"secretlength", b"secretname", b"secretsize", b"tokenfile", b"keyfile",
                b"tokenendpoint", b"tokenuri", b"tokenurl", b"apiendpoint", b"apiuri", b"apiurl")
    if compact.endswith(metadata) or compact in (b"usersecretsid", b"issuerkeyhash", b"keyvaulttostoresecrets"):
        return False
    if compact.endswith((b"publickey", b"pubkey", b"foreignkey", b"primarykey", b"bucketkey",
                         b"naturalkey", b"schemakey", b"sequencekey", b"publictoken", b"csrftoken")):
        return False
    if compact in (b"author", b"accessor", b"withcredentials", b"authenticationresults"):
        return False
    if markers == {b"api"} and (b"rapid" in compact or b"capital" in compact):
        return False
    if markers == {b"key"} and any(word in compact for word in
                                  (b"keyboard", b"keyword", b"monkey", b"donkey", b"turkey", b"keying")):
        return False
    return True


def bindings(data, *, quoted=False):
    """Read identifier/declarator, assignment operator, and a literal value."""
    offset = 0
    while offset < len(data):
        if data[offset] not in IDENTIFIER:
            offset += 1
            continue
        start = offset
        while offset < len(data) and data[offset] in IDENTIFIER:
            offset += 1
        name = data[start:offset]
        cursor = offset
        # The optional declaration suffix handles language type annotations.
        while cursor < min(len(data), offset + 20) and data[cursor] in IDENTIFIER + b" \t":
            cursor += 1
        for _ in range(3):
            if cursor < len(data) and data[cursor] in SPACE + b"'\"":
                cursor += 1
        operators = (b":::=", b"::=", b":=", b"=>", b"?=", b"||", b"=", b">", b":", b",")
        operator = next((item for item in operators if data.startswith(item, cursor)), None)
        if operator is None:
            continue
        cursor += len(operator)
        quote = None
        for _ in range(5):
            if cursor < len(data) and data[cursor] in SPACE + b"`'\"=":
                if data[cursor] in b"`'\"":
                    quote = data[cursor]
                cursor += 1
        value_start = cursor
        if quoted and quote is not None:
            while cursor < len(data) and data[cursor] != quote:
                if data[cursor] == 92 and cursor + 1 < len(data):
                    cursor += 1
                cursor += 1
        else:
            while cursor < len(data) and 33 <= data[cursor] <= 126 and data[cursor] not in b"`'\";":
                cursor += 1
        # A literal needs an actual terminator. A syntactically incomplete
        # identifier or an arbitrary punctuation suffix is not a binding.
        if cursor < len(data) and data[cursor] not in SPACE + b"`'\";":
            if not data.startswith((b"\\n", b"\\r"), cursor):
                continue
        if value_start < cursor:
            yield name, start, value_start, cursor


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
