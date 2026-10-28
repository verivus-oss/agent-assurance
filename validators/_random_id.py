"""OS-random version-four identifiers without platform discovery."""

from os import urandom as _random_bytes


def random_id_hex():
    raw = _random_bytes(16)
    if type(raw) is not bytes or len(raw) != 16:
        raise RuntimeError('random identifier source did not return sixteen bytes')
    value = bytearray(raw)
    value[6] = (value[6] & 15) | 64
    value[8] = (value[8] & 63) | 128
    return value.hex()


def random_id_text():
    value = random_id_hex()
    return '-'.join((value[:8], value[8:12], value[12:16], value[16:20], value[20:]))
