"""Independent public examples and boundary controls for detector components."""

import hashlib
import binascii
import os

from _credential_detection import Capture, entropy, scan_bytes
from _credential_primitives import FileCapture
from _credential_controls import controls, opaque, rejections
from _credential_decoding import View
from _credential_git import git
from _test_require import expect_raises, require
import _toml11 as toml


def test_github():
    # This fixture is public synthetic data, assembled rather than issued.
    body = b"Ab12Cd34Ef56Gh78Ij90Kl12Mn34Op56Qr78"
    value = b"ghp_" + body
    data = b"prefix\x00" + value + b" suffix"
    captures = [item for item in scan_bytes(data) if item.rule == "github-pat"]
    require(len(captures) == 1)
    capture = captures[0]
    require((capture.start, capture.end) == (7, 7 + len(value)))
    require(capture.value_sha256 == hashlib.sha256(value).hexdigest())
    require(set(capture.record()) == {"rule", "byte_span", "context_byte_span", "value_sha256", "source_sha256"})
    require(capture.record()["source_sha256"] == hashlib.sha256(data).hexdigest())
    for rejected in (b"ghp_" + body[:-1], b"ghp_" + b"x" * 36,
                     b"GHP_" + body, b"ghp_" + body[:-1] + b"!", b"ghp_" + b"\xff" * 36):
        require(not any(item.rule == "github-pat" for item in scan_bytes(rejected)))
    for prefix, rule in ((b"gho_", "github-oauth"), (b"ghu_", "github-app-token"),
                         (b"ghs_", "github-app-token"), (b"ghr_", "github-refresh-token")):
        require(any(item.rule == rule for item in scan_bytes(prefix + body)))


def test_bindings():
    value = b"0123456789abcdef"
    accepted = (
        b'token="' + value + b'"', b"API_KEY = '" + value + b"'",
        b'{"client_secret": "' + value + b'"}', b"clientToken string = `" + value + b"`",
        b"myToken := " + value, b"ACCESS_TOKEN ?= " + value,
        b'getEnv("API_TOKEN", "' + value + b'")', b"<apiToken>\n    " + value + b"\n</apiToken>",
    )
    for data in accepted:
        found = [item for item in scan_bytes(data) if item.rule == "generic-api-key"]
        require(len(found) == 1, "independent credential binding was omitted: " + repr(data))
        capture = found[0]
        require(data[capture.start:capture.end] == value)
        require(capture.context_start <= capture.start < capture.end == capture.context_end)
    for name in (b"key_name", b"credential_id", b"public_key", b"secret_length", b"apiVersion",
                 b"author", b"keyword", b"csrf-token", b"issuerKeyHash"):
        require(not scan_bytes(name + b"='" + value + b"'"), "metadata operand became a credential")
    for data in (b"token=base", b"token='allalphabeticcharacters'", b"token=1111111111111111",
                 b"token", b"token='01234'", b"token='0123456789abcde\xff'", b"key_length=1"):
        require(not scan_bytes(data))
    # A metadata context cannot suppress a complete service-token capture.
    body = b"Ab12Cd34Ef56Gh78Ij90Kl12Mn34Op56Qr78"
    require(any(item.rule == "github-pat" for item in scan_bytes(b"key_name=" + b"ghp_" + body)))


def test_capture_boundary():
    require(entropy(b"aaaa") == 0.0)
    require(entropy(b"0123456789abcdef") == 4.0)
    expect_raises(TypeError, lambda: scan_bytes("token=value"), "decoded source was accepted")
    for start, end in ((0, 0), (-1, 1), (0, 4), (2, 1)):
        expect_raises(ValueError, lambda: Capture("control", b"abc", start, end),
                      "invalid credential byte span was accepted")
    for data in (b"", b"public file bytes"):
        capture = FileCapture("pkcs12-file", data)
        require(not isinstance(capture, Capture), "file obligations inherited the nonempty value invariant")
        require(capture.record() == {"rule": "pkcs12-file", "kind": "file", "byte_span": [0, len(data)],
                                     "source_sha256": hashlib.sha256(data).hexdigest()})
        found = [item for item in scan_bytes(data, path=b"public.p12") if item.rule == "pkcs12-file"]
        require(len(found) == 1 and found[0].record() == capture.record())


def test_population():
    with open(os.path.join(os.path.dirname(__file__), "credential-rule-population.toml"), "rb") as source:
        population = toml.loads_bytes(source.read())
    cases = controls()
    required = set(population["rule_ids"])
    require(required and len(required) == len(population["rule_ids"]))
    require({case["rule"] for case in cases} == required)
    require(len({case["id"] for case in cases}) == len(cases))
    observed = set()
    for case in cases:
        captures = scan_bytes(case["source"], path=case["path"])
        found = {capture.rule for capture in captures}
        require(case["rule"] in found, "canonical candidate missed: " + case["id"])
        observed.add(case["rule"])
        for capture in captures:
            record = capture.record()
            require(record["source_sha256"] == hashlib.sha256(case["source"]).hexdigest())
            require(0 <= capture.start <= capture.end <= len(case["source"]))
    require(observed == required, "candidate fixture population did not execute completely")
    rejected = rejections()
    require(rejected and len({case["id"] for case in rejected}) == len(rejected))
    require({case["rule"] for case in rejected} <= observed)
    for case in rejected:
        require(case["rule"] not in {capture.rule for capture in scan_bytes(case["source"], path=case["path"])},
                "malformed provider body accepted: " + case["id"])


def test_rejected_structures():
    good = opaque(40)
    invalid = (
        ("1password-service-account-token", b"ops_eyJ" + opaque(249), None),
        ("aws-access-token", b"AKIA" + b"0" * 16, None),
        ("azure-ad-client-secret", b"Ab38q~" + opaque(32), None),
        ("authress-service-client-access-key", b"sc_client1.ab123.ACC-id12345678." + opaque(40), None),
        ("airtable-personnal-access-token", b"pat" + opaque(14) + b"." + opaque(64, b"0123456789abcdef"), None),
        ("databricks-api-token", b"dapi" + opaque(32, b"0123456789abcdef") + b"-x", None),
        ("privateai-api-token", b'privateai="' + opaque(32, b"ABCDEFGHIJKLMNOPQRSTUVWXYZ") + b'"', None),
        ("dynatrace-api-token", b"dt0c01." + opaque(24) + b"-" + opaque(64), None),
        ("gitlab-pat-routable", b"glpat-" + opaque(26) + b"." + opaque(9), None),
        ("slack-user-token", b"xoxp-" + b"123456789-" * 3 + opaque(30), None),
        ("slack-config-access-token", b"xoxe/xoxp-1-" + opaque(165), None),
        ("slack-config-access-token", b"keyword xoxe.xoxp-\nxoxe\nxoxb-1-" + opaque(165), None),
        ("sourcegraph-access-token", opaque(40, b"0123456789abcdef"), None),
        ("private-key", b"-----BE" + b"GIN PRIVATE KEY-----\n" + opaque(96), None),
        ("curl-auth-user", b'curl ' + b'--' + b'user "operator:${PASSWORD}" https://example.invalid', None),
        ("curl-auth-user", b"curl " + b"-" + b"u user:password", None),
        ("curl-auth-user", b'curl\n\n\n\n\n\n ' + b'--' + b'user "operator:' + good + b'"', None),
        ("curl-auth-header", b'curl -H "Authorization: Bearer $TOKEN"', None),
        ("curl-auth-header", b'notcurl -H "Authorization: Bearer ' + good + b'"', None),
        ("kubernetes-secret-yaml", b"kind: ConfigMap\ndata:\n  password: Zml4dHVyZXBhc3N3b3Jk\n", "fixture.yaml"),
        ("nuget-config-password", b'<add key="Username" value="' + good + b'" />', "nuget.config"),
        ("nuget-config-password", b'<add key="Password" value="' + good + b'" />', "fixture.xml"),
        ("pkcs12-file", b"public filename control", ".p12"),
        ("freemius-secret-key", b"secret_key = 'sk_" + opaque(29) + b"'", "fixture.txt"),
    )
    for rule, source, path in invalid:
        require(rule not in {c.rule for c in scan_bytes(source, path=path)}, "invalid structure accepted: " + rule)
    # Repeated command words and unclosed key headers cannot hide a final
    # real candidate or turn the whole scan into an empty-success control.
    source = b"curl " * 2000 + b"--" + b"user 'operator:" + good + b"'"
    require(any(c.rule == "curl-auth-user" for c in scan_bytes(source)))
    source = (b"-----BE" + b"GIN PRIVATE KEY-----\n") * 2000 + opaque(96) + b"\n-----EN" + b"D PRIVATE KEY-----"
    require(any(c.rule == "private-key" for c in scan_bytes(source)))


def test_decoding():
    value = b"ghp_" + b"Ab12Cd34Ef56Gh78Ij90Kl12Mn34Op56Qr78"
    forms = (
        ("base64", binascii.b2a_base64(value, newline=False)),
        ("hex", binascii.hexlify(value)),
        ("percent", b"".join(b"%" + format(byte, "02X").encode() for byte in value)),
        ("unicode", b"".join(b"\\u" + format(byte, "04x").encode() for byte in value)),
        ("unicode", b" ".join(b"U+" + format(byte, "04X").encode() for byte in value) + b" "),
    )
    for kind, encoded in forms:
        source = b"before\x00 '" + encoded + b"' after"
        matches = [c for c in scan_bytes(source) if c.rule == "github-pat"]
        require(matches, "encoded candidate missed: " + kind)
        capture = matches[0]
        require(capture.value_sha256 == hashlib.sha256(value).hexdigest())
        require(capture.record()["source_sha256"] == hashlib.sha256(source).hexdigest())
        require(capture.decoding is not None and kind in capture.decoding["kinds"])
        require(source[capture.start:capture.end] == encoded)
        require(not any(c.rule == "github-pat" for c in scan_bytes(source, decode_depth=0)))
    encoded = value
    for _ in range(5):
        encoded = binascii.b2a_base64(encoded, newline=False)
    matches = [c for c in scan_bytes(encoded) if c.rule == "github-pat"]
    require(matches and matches[0].decoding["depth"] == 5)
    require(not any(c.rule == "github-pat" for c in scan_bytes(encoded, decode_depth=4)))
    require(not any(c.rule == "github-pat" for c in scan_bytes(binascii.b2a_base64(encoded, newline=False))))
    for depth in (-1, 6, True, "5"):
        expect_raises(ValueError, lambda: scan_bytes(value, decode_depth=depth), "invalid decode depth was accepted")
    for source in (b"%00", b"%ff", b"\\uZZZZ", b"U+XYZW", b"00000000000000000000000000000000"):
        require(View(source).decode() is None, "invalid or nonprintable encoded data was admitted")
    # A transformed name with a literal value still needs decoding provenance.
    generic_value = b"0123456789abcdef"
    source = b"t%6fken='" + generic_value + b"'"
    matches = [c for c in scan_bytes(source) if c.rule == "generic-api-key"]
    require(matches and matches[0].decoding is not None)
    require(source[matches[0].start:matches[0].end] == b"0123456789abcdef")


def test_tracked_python_source_candidates():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    population = [raw for raw in git(root, ["ls-files", "-z"]).split(b"\0") if raw.endswith(b".py")]
    require(population and len(population) == len(set(population)), "tracked Python source population is absent or duplicated")
    visited = set()
    for relative in population:
        path = os.path.join(os.fsencode(root), relative)
        if os.path.islink(path):
            data = os.readlink(path)
        else:
            with open(path, "rb") as source:
                data = source.read()
        require(not scan_bytes(data, path=relative), "tracked Python source contains a complete credential candidate: " + repr(relative))
        visited.add(relative)
    require(visited == set(population), "tracked Python source population did not execute completely")


if __name__ == "__main__":
    test_github()
    test_bindings()
    test_capture_boundary()
    test_population()
    test_rejected_structures()
    test_decoding()
    test_tracked_python_source_candidates()
    print("credential detector components: declared accepted and rejected byte controls passed")
