"""Shared byte predicates and distinct value/file evidence carriers.

Provider parsers depend on this module without importing the detector that
orchestrates them. Value spans are nonempty; file obligations may be empty.
"""

import hashlib
import math


ALNUM = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
WORD = ALNUM + b"_"
IDENTIFIER = WORD + b".-"
GENERIC = WORD + b".=-"
BASE64 = ALNUM + b"+/"
VALUE = GENERIC + b"+/"
SPACE = b" \t\r\n\v\f"


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


class FileCapture:
    """A file-kind obligation, including a legitimately empty file object."""

    __slots__ = ("rule", "start", "end", "context_start", "context_end", "value_sha256", "source_sha256", "decoding")

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
