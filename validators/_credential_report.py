"""Serialize the credential report's closed JSON value population."""

from _json import encode_basestring_ascii


def encode_report(value):
    if value is None:
        return "null"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is int:
        return str(value)
    if isinstance(value, str):
        return encode_basestring_ascii(value)
    if isinstance(value, list):
        return "[" + ",".join(encode_report(item) for item in value) + "]"
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return "{" + ",".join(encode_basestring_ascii(key) + ":" + encode_report(value[key])
                              for key in sorted(value)) + "}"
    raise TypeError("credential report contains an unsupported JSON value")
