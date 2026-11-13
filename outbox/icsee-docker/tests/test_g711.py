"""Unit tests for the G.711 A-law codec (app/g711.py).

Known vectors come straight from the Sun/ITU-T reference algorithm:
encode(0) = 0xD5, encode(-1) = 0x55, decode(0xD5) = +8,
decode(0x55) = -8.
"""

import math

from app import g711


def test_known_vectors():
    assert g711.alaw_encode(b"\x00\x00") == b"\xd5"      # PCM 0
    assert g711.alaw_encode(b"\xff\xff") == b"\x55"      # PCM -1
    assert g711.alaw_decode(b"\xd5") == b"\x08\x00"      # +8
    assert g711.alaw_decode(b"\x55") == b"\xf8\xff"      # -8
    assert g711.alaw_encode(b"\x00\x80") == b"\x2a"      # PCM -32768 -> 0x2A
    assert g711.alaw_encode(b"\xff\x7f") == b"\xaa"      # PCM +32767 -> 0xAA


def test_roundtrip_sine():
    # 800 samples of a sine sweep at several amplitudes; A-law quantisation
    # error is bounded by half a quantisation step: <= max(8, |x|/16 + 8).
    samples = []
    for amp in (100, 1000, 8000, 30000):
        for i in range(200):
            samples.append(int(amp * math.sin(2 * math.pi * i / 50)))
    pcm = b"".join(s.to_bytes(2, "little", signed=True) for s in samples)
    decoded = g711.alaw_decode(g711.alaw_encode(pcm))
    for i, x in enumerate(samples):
        y = int.from_bytes(decoded[2 * i:2 * i + 2], "little", signed=True)
        assert abs(y - x) <= max(8, abs(x) // 16 + 8), (x, y)


def test_lengths_and_errors():
    pcm = b"\x00\x00" * 320
    assert len(g711.alaw_encode(pcm)) == 320
    assert len(g711.alaw_decode(b"\xd5" * 320)) == 640
    try:
        g711.alaw_encode(b"\x00")
    except ValueError:
        pass
    else:
        raise AssertionError("odd-length PCM must raise ValueError")


def test_tables_cover_full_range():
    assert len(g711._ENCODE_TABLE) == 65536
    assert len(g711._DECODE_TABLE) == 256
    # Every decoded value fits in signed 16-bit.
    assert all(-32768 <= v <= 32767 for v in g711._DECODE_TABLE)
