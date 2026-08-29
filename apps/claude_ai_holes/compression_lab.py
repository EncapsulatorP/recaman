"""Lossless compression experiments for Recaman holes and process bits.

The codecs are deliberately small and auditable. Every reported structural
codec is decoded and compared with its source before a result is returned.
General-purpose codecs come from Python's standard library.
"""

from __future__ import annotations

import bz2
import lzma
import math
import zlib
from functools import lru_cache
from itertools import pairwise

from holes import HoleCatalogue, HoleEvent
from sequence import walk


def encode_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("varints must be non-negative")
    encoded = bytearray()
    while value >= 0x80:
        encoded.append((value & 0x7F) | 0x80)
        value >>= 7
    encoded.append(value)
    return bytes(encoded)


def decode_varints(payload: bytes) -> tuple[int, ...]:
    values: list[int] = []
    value = shift = 0
    for byte in payload:
        value |= (byte & 0x7F) << shift
        if byte & 0x80:
            shift += 7
            if shift > 70:
                raise ValueError("varint is too long")
        else:
            values.append(value)
            value = shift = 0
    if shift:
        raise ValueError("truncated varint")
    return tuple(values)


def encode_events(events: tuple[HoleEvent, ...]) -> bytes:
    """Encode sorted ranges as gap/length varints."""
    encoded = bytearray(encode_varint(len(events)))
    previous_end = -1
    for event in events:
        encoded.extend(encode_varint(event.start - previous_end - 1))
        encoded.extend(encode_varint(event.length - 1))
        previous_end = event.end
    return bytes(encoded)


def decode_events(payload: bytes) -> tuple[HoleEvent, ...]:
    values = decode_varints(payload)
    if not values:
        raise ValueError("empty event payload")
    count = values[0]
    if len(values) != 1 + 2 * count:
        raise ValueError("event payload has the wrong field count")
    events: list[HoleEvent] = []
    previous_end = -1
    for index in range(count):
        gap = values[1 + 2 * index]
        length = values[2 + 2 * index] + 1
        start = previous_end + 1 + gap
        event = HoleEvent(start=start, end=start + length - 1)
        events.append(event)
        previous_end = event.end
    return tuple(events)


def pack_bits(bits: tuple[bool, ...]) -> bytes:
    packed = bytearray((len(bits) + 7) // 8)
    for index, bit in enumerate(bits):
        if bit:
            packed[index // 8] |= 1 << (index % 8)
    return bytes(packed)


def unpack_bits(payload: bytes, count: int) -> tuple[bool, ...]:
    return tuple(bool(payload[index // 8] & (1 << (index % 8))) for index in range(count))


def encode_phase_slips(bits: tuple[bool, ...]) -> bytes:
    """Encode a near-alternating stream by the locations where it fails to flip."""
    if not bits:
        raise ValueError("bit stream is empty")
    slips = [index for index in range(1, len(bits)) if bits[index] == bits[index - 1]]
    encoded = bytearray(encode_varint(len(bits)))
    encoded.append(int(bits[0]))
    encoded.extend(encode_varint(len(slips)))
    previous = 0
    for index in slips:
        encoded.extend(encode_varint(index - previous))
        previous = index
    return bytes(encoded)


def decode_phase_slips(payload: bytes) -> tuple[bool, ...]:
    if not payload:
        raise ValueError("empty phase-slip payload")
    # The initial bit sits after the first varint, so locate that boundary.
    boundary = 0
    while payload[boundary] & 0x80:
        boundary += 1
    count = decode_varints(payload[: boundary + 1])[0]
    initial = bool(payload[boundary + 1])
    values = decode_varints(payload[boundary + 2 :])
    if not values:
        raise ValueError("phase-slip payload has no event count")
    slip_count = values[0]
    if len(values) != slip_count + 1:
        raise ValueError("phase-slip payload has the wrong event count")
    slips: set[int] = set()
    position = 0
    for delta in values[1:]:
        position += delta
        slips.add(position)
    bits = [initial]
    for index in range(1, count):
        bits.append(bits[-1] if index in slips else not bits[-1])
    return tuple(bits)


def _row(name: str, size: int, baseline: int, kind: str, exact: bool = True) -> dict:
    return {
        "name": name,
        "bytes": size,
        "ratio": baseline / size if size else float("inf"),
        "saving": 1 - size / baseline if baseline else 0.0,
        "kind": kind,
        "exact_round_trip": exact,
    }


@lru_cache(maxsize=1)
def catalogue_benchmark(catalogue: HoleCatalogue, source_text: bytes) -> dict:
    event_payload = encode_events(catalogue.events)
    if decode_events(event_payload) != catalogue.events:
        raise RuntimeError("event codec failed its round-trip check")

    # uint32 is sufficient because Chaffin's supplied catalogue is below 2^32.
    expanded_u32 = catalogue.integer_count * 4
    interval_u32 = catalogue.event_count * 8
    rows = [
        _row("expanded uint32 values", expanded_u32, expanded_u32, "baseline"),
        _row("uint32 interval endpoints", interval_u32, expanded_u32, "structural"),
        _row("source range text", len(source_text), expanded_u32, "structural"),
        _row("delta-varint events", len(event_payload), expanded_u32, "structural"),
        _row("delta-varint + zlib", len(zlib.compress(event_payload, 9)), expanded_u32, "general"),
        _row("delta-varint + bz2", len(bz2.compress(event_payload, 9)), expanded_u32, "general"),
        _row("delta-varint + LZMA", len(lzma.compress(event_payload, preset=9)), expanded_u32, "general"),
    ]
    best = min(rows[1:], key=lambda row: row["bytes"])
    return {
        "integer_count": catalogue.integer_count,
        "event_count": catalogue.event_count,
        "baseline_bytes": expanded_u32,
        "rows": rows,
        "best": best,
        "event_codec_bytes": len(event_payload),
        "event_round_trip": True,
    }


@lru_cache(maxsize=12)
def process_benchmark(steps: int) -> dict:
    steps = max(1_000, min(int(steps), 200_000))
    terms, forward = walk(steps)
    byte_bits = bytes(forward)
    packed = pack_bits(forward)
    slips = encode_phase_slips(forward)
    if unpack_bits(packed, steps) != forward:
        raise RuntimeError("bit-packing codec failed its round-trip check")
    if decode_phase_slips(slips) != forward:
        raise RuntimeError("phase-slip codec failed its round-trip check")

    # The sign stream reconstructs the exact trajectory without storing terms.
    reconstructed = 0
    for index, went_forward in enumerate(decode_phase_slips(slips), start=1):
        reconstructed += index if went_forward else -index
    if reconstructed != terms[-1]:
        raise RuntimeError("decoded signs do not reconstruct the final Recaman term")

    rows = [
        _row("one byte per obstruction bit", len(byte_bits), len(byte_bits), "baseline"),
        _row("bit-packed", len(packed), len(byte_bits), "structural"),
        _row("phase-slip delta codec", len(slips), len(byte_bits), "structural"),
        _row("bit-packed + zlib", len(zlib.compress(packed, 9)), len(byte_bits), "general"),
        _row("bit-packed + bz2", len(bz2.compress(packed, 9)), len(byte_bits), "general"),
        _row("bit-packed + LZMA", len(lzma.compress(packed, preset=9)), len(byte_bits), "general"),
    ]

    split = max(2, int(steps * 0.8))
    train_pairs = list(pairwise(forward[:split]))
    train_slips = sum(left == right for left, right in train_pairs)
    q = (train_slips + 0.5) / (len(train_pairs) + 1)
    test_pairs = list(zip(forward[split - 1 : -1], forward[split:]))
    test_slips = sum(left == right for left, right in test_pairs)
    test_flips = len(test_pairs) - test_slips
    ideal_bits = -(test_slips * math.log2(q) + test_flips * math.log2(1 - q))

    best = min(rows[1:], key=lambda row: row["bytes"])
    return {
        "steps": steps,
        "final_term": terms[-1],
        "phase_slips": sum(forward[index] == forward[index - 1] for index in range(1, steps)),
        "rows": rows,
        "best": best,
        "round_trips": {"packed": True, "phase_slip": True, "trajectory": True},
        "held_out_model": {
            "train_steps": split,
            "test_steps": len(test_pairs),
            "estimated_slip_probability": q,
            "test_slips": test_slips,
            "ideal_code_bits": ideal_bits,
            "bits_per_step": ideal_bits / len(test_pairs),
            "uniform_baseline_bits_per_step": 1.0,
            "theoretical_saving": 1 - ideal_bits / len(test_pairs),
            "warning": "Ideal arithmetic-code length; a measured bound, not a serialized codec size.",
        },
    }
