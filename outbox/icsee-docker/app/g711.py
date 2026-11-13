"""ITU-T G.711 A-law codec, pure Python (no external dependency).

Implemented from the canonical Sun/ITU-T G.711 reference algorithm
(``linear2alaw`` / ``alaw2linear`` as used in Sun's g711.c):

* encode: 16-bit signed linear PCM -> 8-bit A-law
* decode: 8-bit A-law -> 16-bit signed linear PCM

The camera talkback path (BAO-CAO.md SS2.2) uses G.711 A-law, 8 kHz mono:
the app sends PCM 16-bit 8 kHz and the native SDK encodes it to G.711 A-law
before ``DevSendTalkData``; the DVRIP talkback (go2rtc ``backchannel.go``)
sends G.711 A-law 8 kHz in 320-byte packets. This module provides both
directions so the API can accept PCM16 and emit G.711 A-law (and vice versa
for the microphone stream).

Lookup tables are built once at import (65,536-entry encode table,
256-entry decode table).
"""

_SEG_END = (0xFF, 0x1FF, 0x3FF, 0x7FF, 0xFFF, 0x1FFF, 0x3FFF, 0x7FFF)


def _search(val: int, table=_SEG_END) -> int:
    for i, t in enumerate(table):
        if val <= t:
            return i
    return len(table)


def _linear2alaw(pcm_val: int) -> int:
    """One sample: signed 16-bit linear PCM -> 8-bit A-law."""
    if pcm_val >= 0:
        mask = 0xD5
    else:
        mask = 0x55
        pcm_val = -pcm_val - 1
        if pcm_val < 0:
            pcm_val = 0
    seg = _search(pcm_val)
    if seg >= 8:
        # Out of range: return maximum value.
        return 0xD5 & mask
    aval = seg << 4
    if seg < 2:
        aval |= (pcm_val >> 4) & 0x0F
    else:
        aval |= (pcm_val >> (seg + 3)) & 0x0F
    return aval ^ mask


def _alaw2linear(a_val: int) -> int:
    """One sample: 8-bit A-law -> signed 16-bit linear PCM."""
    a_val ^= 0x55
    t = (a_val & 0x0F) << 4
    seg = (a_val & 0x70) >> 4
    if seg == 0:
        t += 8
    elif seg == 1:
        t += 0x108
    else:
        t += 0x108
        t <<= seg - 1
    return t if (a_val & 0x80) else -t


# Precomputed tables.
_ENCODE_TABLE = bytes(_linear2alaw(v - 32768) for v in range(65536))
_DECODE_TABLE = tuple(_alaw2linear(v) for v in range(256))


def alaw_encode(pcm: bytes) -> bytes:
    """Encode little-endian PCM16 bytes -> G.711 A-law bytes (same length/2)."""
    if len(pcm) % 2:
        raise ValueError("PCM16 input must have an even number of bytes")
    out = bytearray(len(pcm) // 2)
    for i in range(0, len(pcm), 2):
        sample = pcm[i] | (pcm[i + 1] << 8)
        if sample >= 32768:
            sample -= 65536
        out[i // 2] = _ENCODE_TABLE[sample + 32768]
    return bytes(out)


def alaw_decode(g711: bytes) -> bytes:
    """Decode G.711 A-law bytes -> little-endian PCM16 bytes (2x length)."""
    out = bytearray(len(g711) * 2)
    for i, b in enumerate(g711):
        sample = _DECODE_TABLE[b]
        out[2 * i] = sample & 0xFF
        out[2 * i + 1] = (sample >> 8) & 0xFF
    return bytes(out)


def pcm16_to_alaw_samples(samples) -> bytes:
    """Encode an iterable of signed 16-bit ints -> G.711 A-law bytes."""
    return bytes(_ENCODE_TABLE[s + 32768] for s in samples)
