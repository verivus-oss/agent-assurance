"""Bounded diagnostic values and printable control-character escaping."""


def value_summary(value):
    if isinstance(value, str):
        return repr(value[:96]) + ("..." if len(value) > 96 else "")
    if value is None or type(value) in {bool, int, float}:
        return repr(value)
    return "<" + type(value).__name__ + ">"


def printable(message):
    return "".join(f"\\u{ord(character):04x}" if ord(character) < 32 or ord(character) == 127 else character
                   for character in str(message))
