"""Versioned byte decoding with original-source spans and no pattern engine."""

import binascii
from bisect import bisect_right

HEX = b"0123456789abcdefABCDEF"
B64 = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-/+"
SPACE = b" \t\n\r\f"
VERSION = "credential-encodings-v1"


def printable(value):
    # This is the old decoder's exact accepted byte interval, including
    # selected control bytes. It is not a claim about display safety.
    return bool(value) and all(8 < byte < 127 for byte in value)


def run_end(data, start, alphabet):
    end = start
    while end < len(data) and data[end] in alphabet:
        end += 1
    return end


def point(data, start):
    if data[start:start + 2] == b"U+" and start + 6 <= len(data):
        digits, end = data[start + 2:start + 6], start + 6
        if all(byte in HEX for byte in digits) and (end == len(data) or data[end] in SPACE):
            return end + (end < len(data)), int(digits, 16), "unicode-point"
    if data[start:start + 1] == b"\\":
        cursor = start + 1
        if data[cursor:cursor + 1] == b"\\":
            cursor += 1
        if data[cursor:cursor + 1].lower() == b"u" and cursor + 5 <= len(data):
            digits = data[cursor + 1:cursor + 5]
            if all(byte in HEX for byte in digits):
                return cursor + 5, int(digits, 16), "unicode-escape"
    return None


def encoded_segments(data):
    cursor = 0
    while cursor < len(data):
        start = cursor
        if (data[cursor:cursor + 1] == b"%" and cursor + 3 <= len(data)
                and all(byte in HEX for byte in data[cursor + 1:cursor + 3])):
            end = cursor + 3
            limit = data.find(b"\n", end)
            limit = len(data) if limit == -1 else limit
            position = data.find(b"%", end, limit)
            while position != -1:
                if position + 3 <= limit and all(byte in HEX for byte in data[position + 1:position + 3]):
                    end = position + 3
                    # Do not repeatedly rescan the rest of a poisoned line.
                    if not 8 < int(data[position + 1:position + 3], 16) < 127:
                        break
                position = data.find(b"%", position + 1, limit)
            value = bytearray()
            offset, valid = start, True
            while offset < end:
                if (data[offset] == 37 and offset + 3 <= end
                        and all(byte in HEX for byte in data[offset + 1:offset + 3])):
                    byte = int(data[offset + 1:offset + 3], 16)
                    if not 8 < byte < 127:
                        # Retain the invalid escape literally, while decoding
                        # valid neighbors independently on either side.
                        if offset > start:
                            yield start, offset, bytes(value), "percent"
                        end = offset + 3
                        valid = False
                        break
                    value.append(byte)
                    offset += 3
                else:
                    value.append(data[offset])
                    offset += 1
            cursor = end
            if valid:
                yield start, end, bytes(value), "percent"
            continue
        found = point(data, cursor)
        if found is not None:
            value = bytearray()
            notation = found[2]
            while found is not None and found[2] == notation:
                cursor, code, _ = found
                value.extend(("\ufffd" if 0xD800 <= code <= 0xDFFF else chr(code)).encode("utf-8"))
                found = point(data, cursor)
            yield start, cursor, bytes(value), "unicode"
            continue
        if data[cursor] in HEX:
            end = run_end(data, cursor, HEX)
            if end - cursor >= 32:
                raw = data[cursor:end]
                cursor = end
                if len(raw) % 2 == 0 and any(byte in b"0123456789" for byte in raw):
                    decoded = binascii.unhexlify(raw)
                    if printable(decoded):
                        yield start, end, decoded, "hex"
                continue
        if data[cursor] in B64:
            end = run_end(data, cursor, B64)
            if end - cursor >= 16:
                for _ in range(2):
                    if data[end:end + 1] == b"=":
                        end += 1
                raw = data[cursor:end]
                cursor = end
                if not any(byte in b"0123456789+/-_" for byte in raw):
                    continue
                decoded = None
                try:
                    decoded = binascii.a2b_base64(raw, strict_mode=True)
                except binascii.Error:
                    decoded = None
                if decoded is None and b"=" not in raw and all(byte in B64 and byte not in b"+/" for byte in raw):
                    normalized = raw.translate(bytes.maketrans(b"-_", b"+/"))
                    try:
                        decoded = binascii.a2b_base64(normalized + b"=" * ((-len(raw)) % 4), strict_mode=True)
                    except binascii.Error:
                        decoded = None
                if decoded is not None and printable(decoded):
                    yield start, end, decoded, "base64"
                continue
        cursor += 1


class View:
    """Piece table mapping derived byte intervals to original containers."""

    __slots__ = ("data", "origins", "starts", "depth")

    def __init__(self, data, origins=None, depth=0):
        self.data = data
        self.origins = [(0, len(data), 0, len(data), ())] if origins is None else origins
        self.starts = [row[0] for row in self.origins]
        self.depth = depth

    def overlap(self, start, end):
        offset = max(0, bisect_right(self.starts, start) - 1)
        while offset < len(self.origins):
            row = self.origins[offset]
            if row[0] >= end:
                break
            if start < row[1]:
                yield row
            offset += 1

    def clipped(self, start, end, output_start):
        for begin, stop, source_begin, source_stop, kinds in self.overlap(start, end):
            left, right = max(start, begin), min(end, stop)
            if not kinds:
                source_stop = source_begin + right - begin
                source_begin += left - begin
            yield output_start + left - start, output_start + right - start, source_begin, source_stop, kinds

    def source_span(self, start, end):
        rows = list(self.clipped(start, end, 0))
        if not rows:
            raise ValueError("derived capture has no original source interval")
        kinds = tuple(sorted({kind for row in rows for kind in row[4]}))
        return min(row[2] for row in rows), max(row[3] for row in rows), kinds

    def decode(self):
        pieces, origins = [], []
        copied, output_size = 0, 0
        for start, end, decoded, kind in encoded_segments(self.data):
            if not 0 <= copied <= start < end <= len(self.data) or len(decoded) >= end - start:
                raise ValueError("decoder did not produce ordered shrinking byte intervals")
            pieces.append(self.data[copied:start])
            origins.extend(self.clipped(copied, start, output_size))
            output_size += start - copied
            source_start, source_end, kinds = self.source_span(start, end)
            pieces.append(decoded)
            origins.append((output_size, output_size + len(decoded), source_start, source_end,
                            tuple(sorted(set(kinds) | {kind}))))
            output_size += len(decoded)
            copied = end
        if not origins:
            return None
        pieces.append(self.data[copied:])
        origins.extend(self.clipped(copied, len(self.data), output_size))
        return View(b"".join(pieces), origins, self.depth + 1)
