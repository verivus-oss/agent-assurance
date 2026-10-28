"""Independent version/variant bits and native entropy failure controls."""

import _random_id as identifiers
from _test_require import expect_raises, require


def test_identifier_bits_and_shapes():
    original = identifiers._random_bytes
    try:
        for fill in range(256):
            raw = bytes([fill]) * 16
            calls = []

            def supplied(size):
                calls.append(size)
                return raw

            identifiers._random_bytes = supplied
            hexadecimal = identifiers.random_id_hex()
            text = identifiers.random_id_text()
            require(calls == [16, 16])
            require(len(hexadecimal) == 32 and len(text) == 36)
            require(text.split('-') == [hexadecimal[:8], hexadecimal[8:12], hexadecimal[12:16], hexadecimal[16:20], hexadecimal[20:]])
            decoded = bytes.fromhex(hexadecimal)
            require(decoded[6] >> 4 == 4, 'identifier version bits changed')
            require(decoded[8] >> 6 == 2, 'identifier variant bits changed')
            for index, value in enumerate(raw):
                if index == 6:
                    require(decoded[index] & 15 == value & 15)
                elif index == 8:
                    require(decoded[index] & 63 == value & 63)
                else:
                    require(decoded[index] == value)
    finally:
        identifiers._random_bytes = original
    require(len(identifiers.random_id_hex()) == 32)


def test_entropy_failure_boundaries():
    original = identifiers._random_bytes
    try:
        for raw in (b'', bytes(15), bytes(17), bytearray(16), None, 'sixteen'):
            identifiers._random_bytes = lambda _size: raw
            expect_raises(RuntimeError, identifiers.random_id_hex, 'invalid entropy result passed')

        def unavailable(_size):
            raise OSError('entropy unavailable')

        identifiers._random_bytes = unavailable
        expect_raises(OSError, identifiers.random_id_text, 'entropy failure produced an identifier')
    finally:
        identifiers._random_bytes = original


if __name__ == '__main__':
    test_identifier_bits_and_shapes()
    test_entropy_failure_boundaries()
    print('random identifier controls: complete byte-fill population, fixed version/variant bits and entropy failures checked')
