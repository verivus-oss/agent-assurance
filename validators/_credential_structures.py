"""Explicit parsers for compound credential identifiers and containers."""

from bisect import bisect_left, bisect_right

from _credential_primitives import ALNUM, WORD, SPACE, Capture, FileCapture, all_bytes, bindings, entropy, occurrences
from _credential_formats import (BASE64_BODY, DIGITS, HEX, LOWER_HEX, PADDED_BODY,
                                 URL_BODY, boundary, terminated, uuid_body)

TOKEN_BYTES = PADDED_BODY + b"./+~%|:@"


def tail(data, start, alphabet=TOKEN_BYTES, maximum=None):
    end = start
    stop = len(data) if maximum is None else min(len(data), start + maximum)
    while end < stop and data[end] in alphabet:
        end += 1
    return end


def emit(data, rule, start, end, threshold=0, *, left=True, ending=True):
    if start < end <= len(data) and (not left or boundary(data, start)):
        if (not ending or terminated(data, end)) and entropy(data[start:end]) >= threshold:
            yield Capture(rule, data, start, end)


def base64_field(value, minimum, maximum=None, padding=3):
    raw = value.rstrip(b"=")
    return (minimum <= len(raw) and (maximum is None or len(raw) <= maximum)
            and len(value) - len(raw) <= padding and all_bytes(raw, BASE64_BODY))


def onepassword(data):
    upper = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    for start in occurrences(data, b"A3-"):
        for length, sizes in ((39, (2, 6, 11, 5, 5, 5)), (40, (2, 6, 6, 5, 5, 5, 5))):
            end = start + length
            parts = data[start:end].split(b"-")
            if (end <= len(data) and len(parts) == len(sizes)
                    and all(len(part) == size and all_bytes(part, upper) for part, size in zip(parts, sizes))
                    and boundary(data, end)):
                yield from emit(data, "1password-secret-key", start, end, 3.8, ending=False)
    for start in occurrences(data, b"ops_eyJ"):
        end = tail(data, start + 7, BASE64_BODY)
        for _ in range(3):
            if data[end:end + 1] == b"=":
                end += 1
        if base64_field(data[start + 7:end], 250):
            yield from emit(data, "1password-service-account-token", start, end, 4, left=False, ending=False)


def cloud_tokens(data):
    for start in occurrences(data, b"pat"):
        if b"airtable" not in data.lower():
            continue
        end = start + 82
        value = data[start:end]
        if (len(value) == 82 and all_bytes(value[3:17], ALNUM) and value[17:18] == b"."
                and all_bytes(value[18:], LOWER_HEX) and boundary(data, end)):
            yield from emit(data, "airtable-personnal-access-token", start, end, ending=False)
    for prefix in (b"AKIA", b"ASIA", b"ABIA", b"ACCA", b"A3T"):
        for start in occurrences(data, prefix):
            end = start + 20
            key = data[start:end]
            prefix_ok = prefix != b"A3T" or len(key) == 20 and key[3] in b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            if (len(key) == 20 and prefix_ok and all_bytes(key[4:], b"ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
                    and boundary(data, end)):
                yield from emit(data, "aws-access-token", start, end, 3, ending=False)
    for start in occurrences(data, b"ABSK"):
        end = tail(data, start + 4, BASE64_BODY + b"=")
        if base64_field(data[start + 4:end], 109, 269, 2):
            yield from emit(data, "aws-amazon-bedrock-api-key-long-lived", start, end, 3)
    marker = b"bedrock-api-key-" + b"YmVkcm9jay5hbWF6b25hd3MuY29t"
    for start in occurrences(data, marker):
        yield from emit(data, "aws-amazon-bedrock-api-key-short-lived", start, start + len(marker), 3,
                        left=False, ending=False)
    for position in occurrences(data, b"Q~"):
        start = position - 4
        if start < 0:
            continue
        left_ok = start == 0 or data[start - 1] in b"\\'\"` \t\r\n>=:(,"
        if not left_ok or not all_bytes(data[start:start + 3], ALNUM + b"_~.") or data[start + 3] not in DIGITS:
            continue
        end = tail(data, position + 2, ALNUM + b"_~.-", 34)
        if (31 <= end - position - 2 <= 34 and (end == len(data) or data[end] in b"\\'\"` \t\r\n<),")
                and entropy(data[start:end]) >= 3):
            yield Capture("azure-ad-client-secret", data, start, end)
    for prefix in (b"sc_", b"ext_", b"scauth_", b"authress_"):
        for start in occurrences(data, prefix):
            end = tail(data, start)
            parts = data[start + len(prefix):end].split(b".")
            if len(parts) != 4:
                continue
            client, region, account, credential = parts
            if (5 <= len(client) <= 30 and all_bytes(client, ALNUM)
                    and 4 <= len(region) <= 6 and all_bytes(region, ALNUM)
                    and account.startswith((b"acc_", b"acc-"))
                    and 10 <= len(account[4:]) <= 32 and all_bytes(account[4:], ALNUM + b"-")
                    and 30 <= len(credential) <= 120 and all_bytes(credential, ALNUM + b"+/_=-")):
                yield from emit(data, "authress-service-client-access-key", start, end, 2)
    for start in occurrences(data, b"v1.0-"):
        end = start + 176
        value = data[start:end]
        if len(value) == 176 and value[29:30] == b"-" and all_bytes(value[5:29] + value[30:], LOWER_HEX):
            yield from emit(data, "cloudflare-origin-ca-key", start, end, 2)
    for start in occurrences(data, b"dapi"):
        end = start + 36
        if end > len(data) or not all_bytes(data[start + 4:end], LOWER_HEX):
            continue
        if data[end:end + 1] == b"-" and end + 1 < len(data) and data[end + 1] in DIGITS:
            end += 2
        yield from emit(data, "databricks-api-token", start, end, 3)
    for start in occurrences(data, b"dt0c01."):
        end = start + 96
        value = data[start:end]
        if len(value) == 96 and value[31:32] == b"." and all_bytes(value[7:31] + value[32:], ALNUM):
            yield from emit(data, "dynatrace-api-token", start, end, 4, left=False, ending=False)


def provider_compounds(data):
    for prefix, rule in ((b"FLWSECK_TEST-", "flutterwave-encryption-key"),
                         (b"FLWPUBK_TEST-", "flutterwave-public-key"),
                         (b"FLWSECK_TEST-", "flutterwave-secret-key")):
        for start in occurrences(data, prefix):
            size = 12 if rule == "flutterwave-encryption-key" else 32
            body = start + len(prefix)
            end = body + size
            if end > len(data) or not all_bytes(data[body:end], b"abcdefghABCDEFGH0123456789"):
                continue
            if size == 32:
                if data[end:end + 2].lower() != b"-x":
                    continue
                end += 2
            yield from emit(data, rule, start, end, 2, left=False, ending=False)
    for prefix in (b"fo1_", b"fm1a_", b"fm1r_", b"fm2_"):
        for start in occurrences(data, prefix):
            body = start + len(prefix)
            end = tail(data, body, URL_BODY if prefix == b"fo1_" else BASE64_BODY + b"=")
            valid = (end - body == 43 and all_bytes(data[body:end], URL_BODY) if prefix == b"fo1_"
                     else base64_field(data[body:end], 100))
            if valid:
                yield from emit(data, "flyio-access-token", start, end, 4)
    for start in occurrences(data.lower(), b"glc_"):
        end = tail(data, start + 4, BASE64_BODY + b"=")
        if base64_field(data[start + 4:end], 32, 400):
            yield from emit(data, "grafana-cloud-api-token", start, end, 3)
    for start in occurrences(data.lower(), b"eyjrijoi"):
        end = tail(data, start + 8, ALNUM + b"=")
        value = data[start + 8:end]
        if base64_field(value, 70, 400) and all_bytes(value.rstrip(b"="), ALNUM):
            yield from emit(data, "grafana-api-key", start, end, 3)
    for start in occurrences(data.lower(), b"glsa_"):
        end = start + 46
        value = data[start:end]
        if (len(value) == 46 and value[37:38] == b"_" and all_bytes(value[5:37], ALNUM)
                and all_bytes(value[38:], HEX)):
            yield from emit(data, "grafana-service-account-token", start, end, 3)
    for prefix in (b"pat.", b"sat."):
        for start in occurrences(data, prefix):
            end = start + 72
            parts = data[start + 4:end].split(b".")
            if (end <= len(data) and len(parts) == 3 and len(parts[0]) == 22 and all_bytes(parts[0], URL_BODY)
                    and len(parts[1]) == 24 and all_bytes(parts[1], ALNUM)
                    and len(parts[2]) == 20 and all_bytes(parts[2], ALNUM)):
                yield from emit(data, "harness-api-key", start, end, left=False, ending=False)
    for marker in occurrences(data, b".atlasv1."):
        start = marker - 14
        if start < 0 or not all_bytes(data[start:marker], ALNUM):
            continue
        end = tail(data, marker + 9, PADDED_BODY, 70)
        if end - marker - 9 >= 60:
            yield from emit(data, "hashicorp-tf-api-token", start, end, 3.5, left=False, ending=False)
    for start in occurrences(data, b"ntn_"):
        end = start + 50
        if (end <= len(data) and all_bytes(data[start + 4:start + 15], DIGITS)
                and all_bytes(data[start + 15:end], ALNUM)):
            yield from emit(data, "notion-api-token", start, end, 4)
    for prefix in (b"sk-proj-", b"sk-svcacct-", b"sk-admin-", b"sk-"):
        for start in occurrences(data, prefix):
            body = start + len(prefix)
            widths = (20,) if prefix == b"sk-" else (58, 74)
            for left_size in widths:
                middle = body + left_size
                if data[middle:middle + 8] != b"T3BlbkFJ":
                    continue
                for right_size in widths:
                    end = middle + 8 + right_size
                    alphabet = ALNUM if prefix == b"sk-" else URL_BODY
                    if end <= len(data) and all_bytes(data[body:middle] + data[middle + 8:end], alphabet):
                        yield from emit(data, "openai-api-key", start, end, 3)
    for start in occurrences(data, b"PMAK-"):
        end = start + 64
        if (end <= len(data) and data[start + 29:start + 30] == b"-"
                and all_bytes(data[start + 5:start + 29] + data[start + 30:end], HEX)):
            yield from emit(data, "postman-api-token", start, end, 3)
    for start in occurrences(data, b"xkeysib-"):
        end = start + 89
        if (end <= len(data) and data[start + 72:start + 73] == b"-"
                and all_bytes(data[start + 8:start + 72], LOWER_HEX)
                and all_bytes(data[start + 73:end], ALNUM)):
            yield from emit(data, "sendinblue-api-token", start, end, 2)


def structure_tokens(data):
    for detector in (onepassword, cloud_tokens, provider_compounds, bound_compounds,
                     segmented_tokens, jwt_tokens, private_keys, slack_tokens, url_tokens, curl_tokens):
        yield from detector(data)


def file_tokens(data, path):
    if path is None:
        return
    if isinstance(path, str):
        path = path.encode("utf-8", "surrogateescape")
    if not isinstance(path, bytes):
        raise TypeError("credential file identity must be source path bytes or text")
    name = path.rsplit(b"/", 1)[-1].lower()
    if len(name) > 4 and name.endswith((b".p12", b".pfx")):
        yield FileCapture("pkcs12-file", data)
    if name.endswith((b".tf", b".hcl", b".php")):
        for key, context, start, end in bindings(data, quoted=True):
            value = data[start:end]
            if name.endswith((b".tf", b".hcl")) and b"password" in key.lower():
                if (data[start - 1:start] == data[end:end + 1] == b'"' and 8 <= len(value) <= 20
                        and all_bytes(value, PADDED_BODY) and entropy(data[start - 1:end + 1]) >= 2):
                    yield Capture("hashicorp-tf-password", data, start, end, context, end + 1)
            if name.endswith(b".php") and key.lower() == b"secret_key" and value[:3].lower() == b"sk_":
                text = value.decode("utf-8", "replace")
                if (len(text) == 32 and all(char not in " \t\n\f\r" for char in text)
                        and context > 0 and data[context - 1] in b"'\""
                        and data[start - 1:start] in (b"'", b'"') and data[end:end + 1] == data[start - 1:start]):
                    yield Capture("freemius-secret-key", data, start, end, context, end)
    if name.endswith(b"nuget.config"):
        for context, attributes in xml_add_attributes(data):
            keys = [data[start:end].lower() for key, start, end in attributes if key.lower() == b"key"]
            if not any(key in (b"password", b"cleartextpassword") for key in keys):
                continue
            for key, start, end in attributes:
                value = data[start:end]
                if (key.lower() == b"value" and len(value.decode("utf-8", "replace")) >= 8
                        and b"\n" not in value and entropy(value) >= 1):
                    yield Capture("nuget-config-password", data, start, end, context, end)
    if name.endswith((b".yml", b".yaml")):
        yield from kubernetes_fields(data)


def xml_add_attributes(data):
    folded = data.lower()
    for context in occurrences(folded, b"<add"):
        cursor = context + 4
        if cursor == len(data) or data[cursor] not in SPACE:
            continue
        attributes = []
        while cursor < len(data):
            while cursor < len(data) and data[cursor] in SPACE:
                cursor += 1
            if data[cursor:cursor + 2] == b"/>":
                yield context, attributes
                break
            key_start = cursor
            cursor = tail(data, cursor, WORD + b".:-")
            key = data[key_start:cursor]
            while cursor < len(data) and data[cursor] in SPACE:
                cursor += 1
            if not key or data[cursor:cursor + 1] != b"=":
                break
            cursor += 1
            while cursor < len(data) and data[cursor] in SPACE:
                cursor += 1
            if cursor == len(data) or data[cursor] not in b"'\"":
                break
            quote = data[cursor]
            start = cursor + 1
            end = data.find(bytes((quote,)), start)
            if end == -1:
                break
            attributes.append((key, start, end))
            cursor = end + 1


def kubernetes_fields(data):
    folded = data.lower()
    kinds = []
    for start in occurrences(folded, b"kind:"):
        if not boundary(data, start):
            continue
        cursor = start + 5
        while cursor < len(data) and data[cursor] in b" \t":
            cursor += 1
        if data[cursor:cursor + 1] in (b"'", b'"'):
            cursor += 1
        end = cursor + 6
        if folded[cursor:end] == b"secret" and boundary(data, end):
            if data[end:end + 1] in (b"'", b'"'):
                end += 1
            kinds.append((start, end))
    for marker in occurrences(folded, b"data:"):
        if not boundary(data, marker):
            continue
        stop = min(len(data), marker + 5 + 100)
        for position in range(marker + 5, stop):
            if data[position] not in SPACE:
                continue
            cursor = position
            while cursor < len(data) and data[cursor] in SPACE:
                cursor += 1
            start = cursor
            cursor = tail(data, cursor, WORD + b".-")
            if cursor == start or data[cursor:cursor + 1] != b":":
                continue
            cursor += 1
            while cursor < len(data) and data[cursor] in b" \t":
                cursor += 1
            if data[cursor:cursor + 1] in (b"|", b">"):
                cursor += 1
                if data[cursor - 1:cursor] == b">" and data[cursor:cursor + 1] in (b"-", b"+"):
                    cursor += 1
                if cursor == len(data) or data[cursor] not in SPACE:
                    continue
                while cursor < len(data) and data[cursor] in SPACE:
                    cursor += 1
            if data[cursor:cursor + 2] in (b"''", b'""'):
                end = cursor + 2
            elif data[cursor:cursor + 2] == b"{{":
                close = data.find(b"}}", cursor + 2)
                if close == -1 or not all_bytes(data[cursor + 2:close], WORD + b' \t"|$:=,.-'):
                    continue
                end = close + 2
            else:
                if data[cursor:cursor + 1] in (b"'", b'"'):
                    cursor += 1
                body = cursor
                end = tail(data, cursor, BASE64_BODY)
                if end - body < 10:
                    continue
                for _ in range(3):
                    if data[end:end + 1] == b"=":
                        end += 1
                if data[end:end + 1] in (b"'", b'"'):
                    end += 1
            if any(0 <= marker - kind_end <= 200 or 0 <= kind_start - end <= 200
                   for kind_start, kind_end in kinds):
                yield Capture("kubernetes-secret-yaml", data, start, end, min(start, marker), end)


BOUND_PREFIX = (
    ("beamer-api-token", (b"beamer",), b"b_", 44, PADDED_BODY),
    ("dropbox-short-lived-api-token", (b"dropbox",), b"sl.", 135, PADDED_BODY),
    ("gocardless-api-token", (b"gocardless",), b"live_", 40, PADDED_BODY),
    ("lob-api-key", (b"lob",), b"live_", 35, HEX),
    ("lob-api-key", (b"lob",), b"test_", 35, HEX),
    ("lob-pub-api-key", (b"lob",), b"live_pub_", 31, HEX),
    ("lob-pub-api-key", (b"lob",), b"test_pub_", 31, HEX),
    ("mailgun-private-api-token", (b"mailgun",), b"key-", 32, HEX),
    ("mailgun-pub-key", (b"mailgun",), b"pubkey-", 32, HEX),
    ("new-relic-browser-api-token", (b"newrelic", b"new_relic", b"new-relic"), b"NRJS-", 19, HEX),
    ("new-relic-insert-key", (b"newrelic", b"new_relic", b"new-relic"), b"NRII-", 32, ALNUM + b"-"),
    ("new-relic-user-api-key", (b"newrelic", b"new_relic", b"new-relic"), b"NRAK-", 27, ALNUM),
    ("okta-access-token", (b"okta",), b"00", 40, PADDED_BODY),
    ("typeform-api-token", (b"typeform",), b"tfp_", 59, PADDED_BODY + b"."),
    ("yandex-aws-access-token", (b"yandex",), b"YC", 38, URL_BODY),
)


def bound_compounds(data):
    for name, context, start, end in bindings(data):
        name, value = name.lower(), data[start:end]
        for rule, contexts, prefix, length, alphabet in BOUND_PREFIX:
            threshold = 4 if rule == "okta-access-token" else 0
            if (any(item in name for item in contexts) and value.lower().startswith(prefix.lower())
                    and len(value) == len(prefix) + length and all_bytes(value[len(prefix):], alphabet)
                    and entropy(value) >= threshold):
                yield Capture(rule, data, start, end, context, end)
        def found(rule):
            return Capture(rule, data, start, end, context, end)
        if b"dropbox" in name and len(value) == 64 and all_bytes(value[:11], ALNUM):
            if value[11:21].lower() == b"aaaaaaaaaa" and all_bytes(value[21:], PADDED_BODY):
                yield found("dropbox-long-lived-api-token")
        if b"dnkey" in name and len(value) == 85 and value[:6].lower() == b"dnkey-":
            if value[32:33] == b"-" and all_bytes(value[6:32] + value[33:], PADDED_BODY):
                yield found("defined-networking-api-token")
        if b"mailchimp" in name and len(value) == 37:
            if all_bytes(value[:32], HEX) and value[32:35].lower() == b"-us" and all_bytes(value[35:], DIGITS):
                yield found("mailchimp-api-key")
        if b"mailgun" in name and len(value) == 50 and value[32:33] == value[41:42] == b"-":
            if all_bytes(value[:32] + value[33:41] + value[42:], b"abcdefghABCDEFGH0123456789"):
                yield found("mailgun-signing-key")
        if (b"mapbox" in name and len(value) == 86 and value[:3].lower() == b"pk."
                and value[63:64] == b"." and all_bytes(value[3:63] + value[64:], ALNUM)):
            yield found("mapbox-api-token")
        if b"plaid" in name:
            for prefix in (b"access-sandbox-", b"access-development-", b"access-production-"):
                if value.lower().startswith(prefix) and uuid_body(value[len(prefix):]):
                    yield found("plaid-api-token")
        if any(item in name for item in (b"bundle_enterprise__contribsys__com", b"bundle_gems__contribsys__com")):
            if len(value) == 17 and value[8:9] == b":" and all_bytes(value[:8] + value[9:], HEX):
                yield found("sidekiq-secret")
        if b"sumo" in name and len(value) == 14 and value[:2] == b"su":
            if all_bytes(value[2:], ALNUM) and entropy(value) >= 3:
                yield found("sumologic-access-id")
        if b"telegr" in name:
            parts = value.split(b":")
            if (len(parts) == 2 and 5 <= len(parts[0]) <= 16 and all_bytes(parts[0], DIGITS)
                    and len(parts[1]) == 35 and parts[1][:1] == b"A" and all_bytes(parts[1][1:], URL_BODY)):
                yield found("telegram-bot-api-token")
        if b"twitter" in name:
            parts = value.split(b"-")
            if (len(parts) == 2 and 15 <= len(parts[0]) <= 25 and all_bytes(parts[0], DIGITS)
                    and 20 <= len(parts[1]) <= 40 and all_bytes(parts[1], ALNUM)):
                yield found("twitter-access-token")
            if (102 <= len(value) <= 122 and value[:22].lower() == b"a" * 22
                    and all_bytes(value[22:], ALNUM + b"%")):
                yield found("twitter-bearer-token")
        if b"yandex" in name:
            if value[:4].lower() == b"aqvn" and 35 <= len(value[4:]) <= 38 and all_bytes(value[4:], URL_BODY):
                yield found("yandex-api-key")
            parts = value.split(b".")
            if (len(parts) == 3 and parts[0].lower() == b"t1"
                    and 1 <= len(parts[1].rstrip(b"=")) and len(parts[1]) - len(parts[1].rstrip(b"=")) <= 2
                    and all_bytes(parts[1].rstrip(b"="), URL_BODY)
                    and len(parts[2].rstrip(b"=")) == 86 and len(parts[2]) - len(parts[2].rstrip(b"=")) <= 2
                    and all_bytes(parts[2].rstrip(b"="), URL_BODY)):
                yield found("yandex-access-token")
        compact = name.replace(b"_", b"").replace(b"-", b"").replace(b".", b"")
        if b"sonarlogin" in compact or b"sonartoken" in compact:
            body = value[4:] if value[:4].lower() in (b"squ_", b"sqp_", b"sqa_") else value
            if len(body) == 40 and all_bytes(body, PADDED_BODY):
                yield found("sonar-api-token")
        if any(item in name for item in (b"atlassian", b"confluence", b"jira")):
            if len(value) == 24 and all_bytes(value[:20], ALNUM) and all_bytes(value[20:], HEX) and entropy(value) >= 3.5:
                yield found("atlassian-api-token")


def segmented_tokens(data):
    for start in occurrences(data, b"glcbt-"):
        middle = data.find(b"_", start + 6, start + 12)
        if middle != -1 and 1 <= middle - start - 6 <= 5 and all_bytes(data[start + 6:middle], ALNUM):
            end = middle + 21
            if end <= len(data) and all_bytes(data[middle + 1:end], URL_BODY):
                yield from emit(data, "gitlab-cicd-job-token", start, end, 3, left=False, ending=False)
    for prefix, rule in ((b"glpat-", "gitlab-pat-routable"),
                         (b"glrt-t", "gitlab-runner-authentication-token-routable")):
        for start in occurrences(data, prefix):
            body = start + len(prefix)
            if prefix == b"glrt-t":
                if body + 1 >= len(data) or data[body] not in DIGITS or data[body + 1] != 95:
                    continue
                body += 2
            end = tail(data, body, URL_BODY, 300)
            if end - body < 27 or data[end:end + 1] != b".":
                continue
            end += 10
            if (end <= len(data) and all_bytes(data[end - 9:end], b"abcdefghijklmnopqrstuvwxyz0123456789")
                    and boundary(data, end)):
                yield from emit(data, rule, start, end, 4, ending=False)
    for position in occurrences(data, b"_mmk"):
        start, end = position - 36, position + 4
        if (start >= 0 and data[start + 6:start + 7] == b"_"
                and all_bytes(data[start:start + 6] + data[start + 7:position], ALNUM)):
            yield from emit(data, "maxmind-license-key", start, end, 4)
    if b"sgp_" in data.lower() or b"sourcegraph" in data.lower():
        for start in occurrences(data.lower(), b"sgp_"):
            body = start + 4
            if data[body:body + 6].lower() == b"local_":
                body += 6
            elif all_bytes(data[body:body + 16], HEX) and data[body + 16:body + 17] == b"_":
                body += 17
            end = body + 40
            if end <= len(data) and all_bytes(data[body:end], HEX) and boundary(data, end):
                yield from emit(data, "sourcegraph-access-token", start, end, 3)
        offset = 0
        while offset < len(data):
            if data[offset] not in HEX:
                offset += 1
                continue
            start = offset
            offset = tail(data, offset, HEX)
            if offset - start == 40 and boundary(data, offset):
                yield from emit(data, "sourcegraph-access-token", start, offset, 3)
    for start in occurrences(data, b"sntrys_eyJpYXQiO"):
        body = start + len(b"sntrys_eyJpYXQiO")
        separator = data.find(b"_", body, body + 450)
        if separator == -1:
            continue
        header = data[body:separator]
        raw = header.rstrip(b"=")
        if len(header) - len(raw) > 2 or not all_bytes(raw, BASE64_BODY):
            continue
        valid = False
        for marker in (b"LCJyZWdpb25fdXJs", b"InJlZ2lvbl91cmwi", b"cmVnaW9uX3VybCI6"):
            for position in occurrences(raw, marker):
                if 10 <= position <= 200 and 10 <= len(raw) - position - len(marker) <= 200:
                    valid = True
        end = separator + 44
        if valid and end <= len(data) and all_bytes(data[separator + 1:end], BASE64_BODY):
            if end == len(data) or data[end] not in BASE64_BODY:
                yield from emit(data, "sentry-org-token", start, end, 4.5, ending=False)
    if b"facebook" in data.lower() and (b"|" in data or b"%" in data):
        offset = 0
        while offset < len(data):
            if data[offset] not in DIGITS:
                offset += 1
                continue
            start = offset
            offset = tail(data, offset, DIGITS)
            if not 15 <= offset - start <= 16 or data[offset:offset + 1] not in (b"|", b"%"):
                continue
            end = tail(data, offset + 1, URL_BODY, 40)
            if end - offset - 1 >= 27:
                yield from emit(data, "facebook-access-token", start, end, 3)


JWT_HEADER_PREFIXES = (
    b"aGJHY2lPaU", b"aGNIVWlPaU", b"aGNIWWlPaU", b"aGRXUWlPaU", b"aU5qUWlP", b"amNtbDBJanBi",
    b"amRIa2lPaU", b"bGNHc2lPbn", b"bGJtTWlPaU", b"cWEzVWlPaU", b"cWQyc2lPb", b"cGMzTWlPaU",
    b"cGRpSTZJ", b"cmFXUWlP", b"clpYbGZiM0J6SWpwY", b"cmRIa2lPaUp", b"dWIyNWpaU0k2",
    b"d01tTWlP", b"d01uTWlPaU", b"d2NIUWlPaU", b"emRXSWlPaU", b"emRuUWlP", b"MFlXY2lPaU",
    b"MGVYQWlPaUp", b"MWNtd2l", b"MWMyVWlPaUp", b"MlpYSWlPaU", b"MlpYSnphVzl1SWpv", b"NElqb2",
    b"NE5XTWlP", b"NE5YUWlPaU", b"NE5YUWpVekkxTmlJNkl", b"NE5YVWlPaU", b"NmFYQWlPaU",
)


def jwt_tokens(data):
    alphabet = ALNUM + b"/\\_-"
    for start in occurrences(data, b"ey"):
        if not boundary(data, start):
            continue
        header_end = tail(data, start, ALNUM)
        if header_end - start < 19 or data[header_end:header_end + 3] != b".ey":
            continue
        payload_end = tail(data, header_end + 1, alphabet)
        if payload_end - header_end - 1 < 19 or data[payload_end:payload_end + 1] != b".":
            continue
        end = tail(data, payload_end + 1, alphabet)
        for _ in range(2):
            if data[end:end + 1] == b"=":
                end += 1
        parts = data[start:end].split(b".")
        if (len(parts) == 3 and len(parts[0]) >= 19 and all_bytes(parts[0], ALNUM)
                and parts[1].startswith(b"ey") and len(parts[1]) >= 19 and all_bytes(parts[1], alphabet)):
            signature = parts[2].rstrip(b"=")
            if not parts[2] or (len(signature) >= 10 and len(parts[2]) - len(signature) <= 2
                                and all_bytes(signature, alphabet)):
                yield from emit(data, "jwt", start, end, 3)
    for header in JWT_HEADER_PREFIXES:
        prefix = b"ZXlK" + header
        for start in occurrences(data, prefix):
            body = start + len(prefix)
            end = tail(data, body, ALNUM + b"/\\_+-\r\n")
            if end - body >= 40:
                for _ in range(2):
                    if data[end:end + 1] == b"=":
                        end += 1
                yield from emit(data, "jwt-base64", start, end, 2, ending=False)


def private_keys(data):
    folded = data.lower()
    footers = sorted([(position, len(marker)) for marker in (b"key-----", b"key block-----")
                      for position in occurrences(folded, marker)])
    footer_starts = [position for position, _ in footers]
    resume = 0
    for start in occurrences(folded, b"-----begin"):
        if start < resume:
            continue
        label_end = folded.find(b"-----", start + 10, start + 130)
        if label_end == -1:
            continue
        label = folded[start + 10:label_end]
        suffix = b"private key block" if label.endswith(b"private key block") else b"private key"
        if not label.endswith(suffix):
            continue
        before = label[:-len(suffix)]
        if len(before) > 100 or before and not all_bytes(before, ALNUM + b" _-"):
            continue
        index = bisect_left(footer_starts, label_end + 5 + 64)
        if index < len(footers):
            position, length = footers[index]
            end = position + length
            resume = end
            yield Capture("private-key", data, start, end)


def slack_tokens(data):
    folded = data.lower()
    for start in occurrences(folded, b"xapp-"):
        first = start + 5
        if first + 1 >= len(data) or data[first] not in DIGITS or data[first + 1] != 45:
            continue
        middle = tail(data, first + 2, ALNUM)
        if middle == first + 2 or data[middle:middle + 1] != b"-":
            continue
        number = tail(data, middle + 1, DIGITS)
        if number == middle + 1 or data[number:number + 1] != b"-":
            continue
        end = tail(data, number + 1, ALNUM)
        if end > number + 1:
            yield from emit(data, "slack-app-token", start, end, 2, left=False, ending=False)
    for start in occurrences(data, b"xoxb-"):
        first = tail(data, start + 5, DIGITS)
        if data[first:first + 1] != b"-":
            continue
        if 8 <= first - start - 5 <= 14:
            end = tail(data, first + 1, ALNUM, 26)
            if end - first - 1 >= 18:
                yield from emit(data, "slack-legacy-bot-token", start, end, 2, left=False, ending=False)
        if 10 <= first - start - 5 <= 13:
            number = tail(data, first + 1, DIGITS)
            if number - first - 1 >= 10:
                end = tail(data, first + 1, ALNUM + b"-")
                yield from emit(data, "slack-bot-token", start, end, 3, left=False, ending=False)
    for prefix, rule in ((b"xoxp-", "slack-user-token"), (b"xoxe-", "slack-user-token"),
                         (b"xoxo-", "slack-legacy-token"), (b"xoxs-", "slack-legacy-token")):
        for start in occurrences(data, prefix):
            cursor = start + 5
            valid = True
            for _ in range(3):
                end = tail(data, cursor, DIGITS)
                size = end - cursor
                if (not size or rule == "slack-user-token" and not 10 <= size <= 13
                        or data[end:end + 1] != b"-"):
                    valid = False
                    break
                cursor = end + 1
            if valid:
                alphabet = ALNUM + b"-" if rule == "slack-user-token" else HEX
                end = tail(data, cursor, alphabet, 34 if rule == "slack-user-token" else None)
                if (end - cursor >= 28 if rule == "slack-user-token" else end > cursor):
                    yield from emit(data, rule, start, end, 2, left=False, ending=False)
    for prefix in (b"xoxa-", b"xoxr-"):
        for start in occurrences(data, prefix):
            cursor = start + 5
            if cursor + 1 < len(data) and data[cursor] in DIGITS and data[cursor + 1] == 45:
                cursor += 2
            end = tail(data, cursor, ALNUM, 48)
            if end - cursor >= 8:
                yield from emit(data, "slack-legacy-workspace-token", start, end, 2, left=False, ending=False)
    for start in occurrences(folded, b"xoxe-"):
        body = start + 5
        if body + 1 < len(data) and data[body] in DIGITS and data[body + 1] == 45:
            end = body + 2 + 146
            if end <= len(data) and all_bytes(data[body + 2:end], ALNUM):
                yield from emit(data, "slack-config-refresh-token", start, end, 2, left=False, ending=False)
    # Preserve the reference detector's literal keyword prerequisite and
    # one-character separator, including candidates beside a keyword hint.
    if any(prefix in folded for prefix in (b"xoxe.xoxb-", b"xoxe.xoxp-")):
        for start in occurrences(folded, b"xoxe"):
            separator = start + 4
            if separator == len(data) or data[separator] == 10:
                continue
            width = 1
            if data[separator] >= 128:
                for size in (2, 3, 4):
                    raw_character = data[separator:separator + size]
                    character = raw_character.decode("utf-8", "replace")
                    if len(character) == 1 and character.encode("utf-8") == raw_character:
                        width = size
                        break
            marker = separator + width
            if folded[marker:marker + 5] not in (b"xoxb-", b"xoxp-"):
                continue
            body = marker + 5
            if body + 1 < len(data) and data[body] in DIGITS and data[body + 1] == 45:
                end = tail(data, body + 2, ALNUM, 166)
                if end - body - 2 >= 163:
                    yield from emit(data, "slack-config-access-token", start, end, 2, left=False, ending=False)


def url_tokens(data):
    for domain in (b"hooks.slack.com/services/", b"hooks.slack.com/workflows/", b"hooks.slack.com/triggers/"):
        for start in occurrences(data, domain):
            end = tail(data, start + len(domain), BASE64_BODY, 56)
            if end - start - len(domain) >= 43:
                begin = start - 8 if data[max(0, start - 8):start] == b"https://" else start
                if begin == start and data[max(0, start - 7):start] == b"http://":
                    begin = start - 7
                yield Capture("slack-webhook-url", data, begin, end)
    folded = data.lower()
    for start in occurrences(folded, b"http"):
        prefix = 8 if folded.startswith(b"https://", start) else 7 if folded.startswith(b"http://", start) else None
        if prefix is None or not boundary(data, start):
            continue
        user = start + prefix
        host = user + 18
        if (data[user + 8:user + 9] == b":" and data[user + 17:user + 18] == b"@"
                and all_bytes(data[user:user + 8] + data[user + 9:user + 17], HEX)):
            for domain in (b"gems.contribsys.com", b"enterprise.contribsys.com"):
                end = host + len(domain)
                if folded[host:end] == domain and (end == len(data) or data[end] in b"/|#?:"):
                    yield Capture("sidekiq-sensitive-url", data, user, user + 17, start, end)
    marker = b".webhook.office.com/webhookb2/"
    for position in occurrences(data, marker):
        host_start = position
        while host_start > 0 and data[host_start - 1] in b"abcdefghijklmnopqrstuvwxyz0123456789":
            host_start -= 1
        if host_start == position or data[max(0, host_start - 8):host_start] != b"https://":
            continue
        body = position + len(marker)
        end = body + 36 + 1 + 36 + len(b"/IncomingWebhook/") + 32 + 1 + 36
        value = data[body:end]
        first = value[:36].split(b"-")
        second = value[37:73].split(b"-")
        third = value[-36:].split(b"-")
        def guid(parts):
            return len(parts) == 5 and all(len(part) == size and all_bytes(part, b"abcdefghijklmnopqrstuvwxyz0123456789")
                                            for part, size in zip(parts, (8, 4, 4, 4, 12)))
        if (end <= len(data) and value[36:37] == b"@" and value[73:90] == b"/IncomingWebhook/"
                and all_bytes(value[90:122], b"abcdefghijklmnopqrstuvwxyz0123456789") and value[122:123] == b"/"
                and guid(first) and guid(second) and guid(third)):
            yield Capture("microsoft-teams-webhook", data, host_start - 8, end)


def shell_argument(data, start, limit):
    cursor, quote = start, None
    decoded = bytearray()
    while cursor < limit:
        char = data[cursor]
        if quote is None and (char in SPACE or char in b";|&"):
            break
        if char in b"'\"" and (quote is None or quote == char):
            quote = char if quote is None else None
        elif char == 92 and quote != 39 and cursor + 1 < limit:
            cursor += 1
            if data[cursor] not in b"\r\n":
                decoded.append(data[cursor])
        else:
            decoded.append(char)
        cursor += 1
    return None if quote is not None else (cursor, bytes(decoded))


def variable_reference(value):
    if value.startswith(b"$"):
        body = value[1:]
        if body.startswith(b"{") and body.endswith(b"}"):
            body = body[1:-1]
        return all_bytes(body, WORD) or body.startswith((b"{", b"("))
    return value.startswith((b"{{", b"[", b"<"))


def curl_user(value, quote):
    user, separator, password = value.partition(b":")
    if not separator or variable_reference(password):
        return False
    if password.lower() in (b"changeit", b"changeme", b"pass", b"password", b"pwd", b"test", b"token"):
        return False
    if password and all(byte == password[0] for byte in password) and password[0] in b"*x":
        return False
    if quote == 34:
        valid = (not user and len(password) >= 3 or len(user) >= 3 and not password
                 or len(user) >= 3 and len(password) >= 3)
    elif quote == 39:
        valid = len(user) >= 3 and len(password) >= 3
    else:
        valid = bool(user) and bool(password)
    return valid and entropy(value) >= 2


def curl_header(value):
    name, separator, content = value.partition(b":")
    if not separator:
        return False
    content = content.lstrip(b" \t")
    basic = False
    if name.lower() == b"authorization":
        for scheme in (b"basic", b"bearer", b"api-token", b"token"):
            if content[:len(scheme)].lower() == scheme and content[len(scheme):len(scheme) + 1] in (b" ", b"\t"):
                basic = scheme == b"basic"
                content = content[len(scheme) + 1:]
                break
    else:
        options = [name.lower()]
        if name.lower().startswith(b"x-"):
            rest = name.lower()[2:]
            options = [rest]
            first, dash, remainder = rest.partition(b"-")
            if dash and all_bytes(first, b"abcdefghijklmnopqrstuvwxyz"):
                options.append(remainder)
        recognized = False
        for option in options:
            for prefix in (b"api-", b"api", b""):
                if option.startswith(prefix) and option[len(prefix):] in (b"key", b"token"):
                    recognized = True
        if not recognized:
            return False
    if basic:
        valid = base64_field(content, 8)
    else:
        valid = len(content) >= 8 and all_bytes(content, WORD + b"=~@.+/-")
    return valid and entropy(content) >= 2.75


def curl_tokens(data):
    commands = [start for start in occurrences(data, b"curl")
                if boundary(data, start) and boundary(data, start + 4)]
    if not commands:
        return
    separators = list(occurrences(data, b"\n"))
    flags = sorted((position, option) for option in (b"--header", b"--user", b"-H", b"-u")
                   for position in occurrences(data, option)
                   if position > 0 and data[position - 1] in b" \t\r\n")
    for position, option in flags:
        index = bisect_right(commands, position) - 1
        if index < 0:
            continue
        context = commands[index]
        first_separator = bisect_left(separators, context)
        if bisect_left(separators, position) - first_separator > 5:
            continue
        limit = separators[first_separator + 5] if first_separator + 5 < len(separators) else len(data)
        start = position + len(option)
        if data[start:start + 1] == b"=":
            start += 1
        else:
            for _ in range(5):
                if start < limit and data[start] in b" \t":
                    start += 1
        argument = shell_argument(data, start, limit)
        if argument is None:
            continue
        end, value = argument
        if end == start:
            continue
        header = option in (b"-H", b"--header")
        quote = data[start] if start < len(data) and data[start] in b"'\"" else None
        if header and quote is not None and curl_header(value):
            yield Capture("curl-auth-header", data, start, end, context, end)
        elif not header and curl_user(value, quote):
            yield Capture("curl-auth-user", data, start, end, context, end)
