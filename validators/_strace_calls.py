"""Parse the syscall name and arguments from selected strace records."""


def _ascii_identifier(char: str) -> bool:
    return char == "_" or "a" <= char <= "z" or "A" <= char <= "Z" or "0" <= char <= "9"


def parsed_calls(trace: str) -> list[tuple[str, str]]:
    calls = []
    for line in trace.splitlines():
        text = line.lstrip(" ")
        if text.startswith("[pid "):
            close = text.find("]")
            if close < 0 or not text[5:close].strip(" ").isascii() or not text[5:close].strip(" ").isdigit():
                continue
            text = text[close + 1:].lstrip(" ")
        else:
            prefix, separator, remainder = text.partition(" ")
            if separator and prefix.isascii() and prefix.isdigit():
                text = remainder.lstrip(" ")
        opening = text.find("(")
        if opening <= 0 or not all(_ascii_identifier(char) for char in text[:opening]):
            continue
        calls.append((text[:opening], text[opening + 1:]))
    return calls
