"""Explicit ASCII predicates shared by the reference validators."""


def ascii_lower(value: str) -> bool:
    return "a" <= value <= "z" and len(value) == 1


def ascii_upper(value: str) -> bool:
    return "A" <= value <= "Z" and len(value) == 1


def ascii_digit(value: str) -> bool:
    return "0" <= value <= "9" and len(value) == 1


def ascii_hex_lower(value: str) -> bool:
    return ascii_digit(value) or "a" <= value <= "f" and len(value) == 1


def valid_hex(value: str, length: int) -> bool:
    return len(value) == length and all(ascii_hex_lower(char) for char in value)


def valid_sha256(value: str) -> bool:
    return value.startswith("sha256:") and valid_hex(value[7:], 64)


def valid_digest(value: str) -> bool:
    algorithm, separator, digest = value.partition(":")
    lengths = {"sha256": 64, "sha384": 96, "sha512": 128}
    return bool(separator) and algorithm in lengths and valid_hex(digest, lengths[algorithm])


def split_closure_root(value: str) -> tuple[str, str] | None:
    algorithm, separator, digest = value.partition(":")
    if (
        not separator
        or not algorithm
        or not digest
        or not all(ascii_lower(char) or ascii_digit(char) for char in algorithm)
        or not all(ascii_hex_lower(char) for char in digest)
    ):
        return None
    return algorithm, digest


def valid_header_name(value: str) -> bool:
    return bool(value) and (ascii_lower(value[0]) or ascii_digit(value[0])) and all(
        ascii_lower(char) or ascii_digit(char) or char == "-" for char in value[1:]
    )


def valid_operation(value: str) -> bool:
    return 1 <= len(value) <= 64 and (
        ascii_lower(value[0]) or ascii_digit(value[0])
    ) and all(
        ascii_lower(char) or ascii_digit(char) or char in "._-" for char in value[1:]
    )


def valid_scheme(value: str) -> bool:
    return bool(value) and ascii_lower(value[0]) and all(
        ascii_lower(char) or ascii_digit(char) or char in "+.-" for char in value[1:]
    )


def valid_assertion_id(value: str) -> bool:
    return value.startswith("A-") and len(value) >= 3 and (
        ascii_lower(value[2]) or ascii_upper(value[2]) or ascii_digit(value[2])
    ) and all(
        ascii_lower(char) or ascii_upper(char) or ascii_digit(char) or char in "_-"
        for char in value[3:]
    )


def valid_observed_line(value: str) -> bool:
    before, separator, after = value.partition("=")
    if not separator or not valid_assertion_id(before.rstrip(" \t\n\r\f")):
        return False
    right = after.strip(" \t\n\r\f")
    return (
        right.startswith("observed(")
        and right.endswith(")")
        and bool(right[len("observed("):-1])
        and ")" not in right[len("observed("):-1]
    )


def valid_closure_field(value: str) -> bool:
    return all(
        part and all(
            ascii_lower(char) or ascii_upper(char) or ascii_digit(char) or char in "_-"
            for char in part
        )
        for part in value.split(".")
    )


def valid_abstraction_id(value: str) -> bool:
    base, separator, version = value.rpartition(".v")
    return bool(separator and base and version) and (
        ascii_lower(base[0]) or ascii_digit(base[0])
    ) and all(
        ascii_lower(char) or ascii_digit(char) or char in "._-" for char in base[1:]
    ) and all(ascii_digit(char) for char in version)


def valid_unprefixed_name(value: str) -> bool:
    return bool(value) and ascii_lower(value[0]) and all(
        ascii_lower(char) or ascii_digit(char) or char == "-" for char in value[1:]
    )


def valid_reverse_dns(value: str) -> bool:
    parts = value.split(".")
    return len(parts) >= 2 and all(valid_unprefixed_name(part) for part in parts)


def valid_semver(value: str) -> bool:
    parts = value.split(".")
    return len(parts) == 3 and all(
        part and (len(part) == 1 or part[0] != "0")
        and all(ascii_digit(char) for char in part)
        for part in parts
    )


def valid_date(value: str) -> bool:
    return len(value) == 10 and value[4] == "-" and value[7] == "-" and all(
        ascii_digit(value[index]) for index in (0, 1, 2, 3, 5, 6, 8, 9)
    )


def valid_datetime(value: str) -> bool:
    if (
        len(value) < 20
        or not valid_date(value[:10])
        or value[10] not in "Tt"
        or value[13] != ":"
        or value[16] != ":"
        or not all(ascii_digit(value[index]) for index in (11, 12, 14, 15, 17, 18))
    ):
        return False
    position = 19
    if value[position] == ".":
        position += 1
        start = position
        while position < len(value) and ascii_digit(value[position]):
            position += 1
        if position == start or position == len(value):
            return False
    suffix = value[position:]
    return suffix in ("Z", "z") or (
        len(suffix) == 6
        and suffix[0] in "+-"
        and suffix[3] == ":"
        and all(ascii_digit(char) for char in suffix[1:3] + suffix[4:])
    )


def valid_index_timestamp(value: str) -> bool:
    if not valid_datetime(value):
        return False
    if value.endswith(("Z", "z")):
        return True
    return int(value[-5:-3]) <= 23 and int(value[-2:]) <= 59


def valid_cost_timestamp(value: str) -> bool:
    if not valid_datetime(value) or value[10] != "T":
        return False
    return not value.endswith("z")


def valid_rfc3339_utc_shape(value: str) -> bool:
    if (
        len(value) < 20
        or not valid_date(value[:10])
        or value[10] != "T"
        or value[13] != ":"
        or value[16] != ":"
        or not all(ascii_digit(value[index]) for index in (11, 12, 14, 15, 17, 18))
    ):
        return False
    if value[19:] == "Z":
        return True
    fraction = value[19:-1]
    return (
        value.endswith("Z")
        and 2 <= len(fraction) <= 10
        and fraction[0] == "."
        and all(ascii_digit(char) for char in fraction[1:])
    )


def valid_upper_prefix(value: str) -> bool:
    return bool(value) and ascii_upper(value[0]) and all(
        ascii_upper(char) or ascii_digit(char) or char == "_" for char in value[1:]
    )


def matches_decimal_id(prefix: str, optional_lower_suffix: bool, value: str) -> bool:
    if not prefix or not value.startswith(prefix):
        return False
    suffix = value[len(prefix):]
    position = 0
    while position < len(suffix) and ascii_digit(suffix[position]):
        position += 1
    if position == 0:
        return False
    tail = suffix[position:]
    return not tail or (optional_lower_suffix and len(tail) == 1 and ascii_lower(tail))
