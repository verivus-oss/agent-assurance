"""Explicit JSON syntax and native value/encoding primitives without fallbacks.

Validate the complete value before calling the C scanner. Its malformed-input
path imports the standard decoder, whose initialization loads regex support.
Only the validated value interval reaches the native scanner.
"""

import hashlib
import _json
import sys


WHITESPACE = " \t\n\r"
_SCANNER = _json.make_scanner
_ENCODER = _json.make_encoder
_STRING = _json.encode_basestring
_ASCII = _json.encode_basestring_ascii


class InvalidJSON(ValueError):
    """An original source identity and byte span, without parser coordinates."""

    def __init__(self, source, position, end=None):
        if isinstance(source, bytes):
            raw = source
            start = position
            stop = min(len(raw), position + 1) if end is None else end
        else:
            raw = source.encode("utf-8", errors="surrogatepass")
            start = len(source[:position].encode("utf-8", errors="surrogatepass"))
            stop = min(len(raw), start + len(source[position:position + 1].encode("utf-8", errors="surrogatepass")))
        self.source_sha256 = hashlib.sha256(raw).hexdigest()
        self.byte_span = (start, stop)
        super().__init__(f"invalid JSON (source sha256 {self.source_sha256}, bytes {start}:{stop})")


def _require_native():
    if (sys.implementation.name != "cpython" or type(_SCANNER) is not type
            or type(_ENCODER) is not type or type(_STRING) is not type(abs)
            or type(_ASCII) is not type(abs)):
        raise RuntimeError("native JSON primitives require compiled CPython implementations")
    for name, expected in (("make_scanner", _SCANNER), ("make_encoder", _ENCODER),
                           ("encode_basestring", _STRING), ("encode_basestring_ascii", _ASCII)):
        if getattr(_json, name, None) is not expected or getattr(expected, "__module__", None) != "_json":
            raise RuntimeError("native JSON primitive is unavailable: " + name)


def _spacing(source, position):
    while position < len(source) and source[position] in WHITESPACE:
        position += 1
    return position


def _string_end(source, position, strict):
    position += 1
    while position < len(source):
        character = source[position]
        if character == '"':
            return position + 1
        if character == "\\":
            position += 1
            if position == len(source):
                raise InvalidJSON(source, position)
            character = source[position]
            if character == "u":
                position += 1
                for _ in range(4):
                    if position == len(source) or source[position] not in "0123456789abcdefABCDEF":
                        raise InvalidJSON(source, position)
                    position += 1
                continue
            if character not in '"\\/bfnrt':
                raise InvalidJSON(source, position)
        elif strict and ord(character) < 32:
            raise InvalidJSON(source, position)
        position += 1
    raise InvalidJSON(source, position)


def _number_end(source, position):
    if source[position] == "-":
        position += 1
    if position == len(source):
        raise InvalidJSON(source, position)
    if source[position] == "0":
        position += 1
    elif source[position] in "123456789":
        position += 1
        while position < len(source) and source[position] in "0123456789":
            position += 1
    else:
        raise InvalidJSON(source, position)
    if position < len(source) and source[position] == ".":
        position += 1
        start = position
        while position < len(source) and source[position] in "0123456789":
            position += 1
        if position == start:
            raise InvalidJSON(source, position)
    if position < len(source) and source[position] in "eE":
        position += 1
        if position < len(source) and source[position] in "+-":
            position += 1
        start = position
        while position < len(source) and source[position] in "0123456789":
            position += 1
        if position == start:
            raise InvalidJSON(source, position)
    return position


def _validated_interval(source, strict):
    """Walk the complete JSON grammar using an explicit container stack."""
    position = _spacing(source, 0)
    start = position
    stack = []
    need_value = True
    while True:
        if not need_value and not stack:
            end = position
            tail = _spacing(source, end)
            if tail != len(source):
                raise InvalidJSON(source, tail)
            return start, end
        position = _spacing(source, position)
        if need_value:
            if position == len(source):
                raise InvalidJSON(source, position)
            character = source[position]
            if character == "{":
                stack.append("object-first")
                position += 1
            elif character == "[":
                stack.append("array-first")
                position += 1
            elif character == '"':
                position = _string_end(source, position, strict)
            else:
                literal = next((value for value in ("null", "true", "false", "NaN", "Infinity", "-Infinity")
                                if source.startswith(value, position)), None)
                if literal is not None:
                    position += len(literal)
                elif character in "-0123456789":
                    position = _number_end(source, position)
                else:
                    raise InvalidJSON(source, position)
            need_value = False
            continue
        state = stack[-1]
        if position == len(source):
            raise InvalidJSON(source, position)
        character = source[position]
        if state in ("object-first", "object-key"):
            if character == "}" and state == "object-first":
                stack.pop()
                position += 1
                continue
            if character != '"':
                raise InvalidJSON(source, position)
            position = _spacing(source, _string_end(source, position, strict))
            if position == len(source) or source[position] != ":":
                raise InvalidJSON(source, position)
            position += 1
            stack[-1] = "object-next"
            need_value = True
        elif state == "object-next":
            if character == "}":
                stack.pop()
                position += 1
            elif character == ",":
                stack[-1] = "object-key"
                position += 1
            else:
                raise InvalidJSON(source, position)
        elif state == "array-first":
            if character == "]":
                stack.pop()
                position += 1
            else:
                stack[-1] = "array-next"
                need_value = True
        elif state == "array-next":
            if character == "]":
                stack.pop()
                position += 1
            elif character == ",":
                position += 1
                need_value = True
            else:
                raise InvalidJSON(source, position)
        else:
            raise RuntimeError("JSON syntax state is unsupported")


def _constant(value):
    return {"NaN": float("nan"), "Infinity": float("inf"), "-Infinity": -float("inf")}[value]


class _Context:
    def __init__(self, *, strict=True, object_hook=None, object_pairs_hook=None,
                 parse_int=None, parse_float=None, parse_constant=None):
        self.strict = bool(strict)
        self.object_hook = object_hook
        self.object_pairs_hook = object_pairs_hook
        self.parse_int = int if parse_int is None else parse_int
        self.parse_float = float if parse_float is None else parse_float
        self.parse_constant = _constant if parse_constant is None else parse_constant
        for hook in (self.object_hook, self.object_pairs_hook, self.parse_int, self.parse_float, self.parse_constant):
            if hook is not None and not callable(hook):
                raise TypeError("JSON value hook must be callable")


def loads(source, **options):
    _require_native()
    # Both readers must see the same built-in source buffer. Subclass methods
    # must not present different syntax to the guard and the native scanner.
    if issubclass(type(source), bytes):
        source = bytes.__bytes__(source)
        invalid = None
        try:
            text = source.decode("utf-8")
        except UnicodeDecodeError as error:
            invalid = (error.start, error.end)
        if invalid is not None:
            raise InvalidJSON(source, *invalid)
        source = text
    if not issubclass(type(source), str):
        raise TypeError("JSON source must be text or UTF-8 bytes")
    source = str.__str__(source)
    context = _Context(**options)
    start, expected_end = _validated_interval(source, context.strict)
    value, end = _SCANNER(context)(source, start)
    if end != expected_end:
        raise RuntimeError("native JSON value interval differs from validated syntax")
    return value


def _unsupported(value):
    raise TypeError("value is not JSON serializable: " + type(value).__name__)


def _indented(compact, unit, item_separator, key_separator):
    result = []
    depth = 0
    quoted = False
    escaped = False
    previous = None
    for position, character in enumerate(compact):
        if quoted:
            result.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
            result.append(character)
        elif character in "{[":
            depth += 1
            result.append(character)
            if compact[position + 1:position + 2] not in ("}", "]"):
                result.extend(("\n", unit * depth))
        elif character in "}]":
            depth -= 1
            if previous not in ("{", "["):
                result.extend(("\n", unit * depth))
            result.append(character)
        elif character == ",":
            result.extend((item_separator, "\n", unit * depth))
        elif character == ":":
            result.append(key_separator)
        else:
            result.append(character)
        previous = character
    if depth != 0 or quoted or escaped:
        raise RuntimeError("native JSON encoder returned incomplete structure")
    return "".join(result)


def dumps(value, *, ensure_ascii=True, check_circular=True, allow_nan=True,
          sort_keys=False, skipkeys=False, indent=None, separators=None, default=None):
    _require_native()
    if indent is not None and not isinstance(indent, (str, int)):
        raise TypeError("JSON indent must be an integer or string")
    if separators is None:
        item_separator, key_separator = (", ", ": ") if indent is None else (",", ": ")
    else:
        if not isinstance(separators, (list, tuple)) or len(separators) != 2 or any(not isinstance(item, str) for item in separators):
            raise TypeError("JSON separators must contain two strings")
        item_separator, key_separator = separators
    if default is not None and not callable(default):
        raise TypeError("JSON default must be callable")
    native_item, native_key = (item_separator, key_separator) if indent is None else (",", ":")
    encoder = _ENCODER({} if check_circular else None, _unsupported if default is None else default,
                       _ASCII if ensure_ascii else _STRING, None, native_key, native_item,
                       sort_keys, skipkeys, allow_nan)
    compact = "".join(encoder(value, 0))
    if indent is None:
        return compact
    unit = indent if isinstance(indent, str) else " " * indent
    return _indented(compact, unit, item_separator, key_separator)


def dump(value, output, **options):
    output.write(dumps(value, **options))
