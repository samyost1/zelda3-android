#!/usr/bin/env python3
"""Build the PT-BR ROM -> vanilla assets BPS using locally supplied ROMs.

Only the BPS is written. Translation text/font are extracted on-device; this
patch reconstructs exactly the baseline produced by the bundled US BPS.
Uses Python's standard library and deterministic SourceCopy/TargetRead output.
"""

import argparse
import hashlib
from pathlib import Path
import struct
import zipfile
import zlib


US_SHA1 = "6D4F10A8B10E10DBE624CB23CF03B88BB8252973"
PT_SHA1 = "D0D09ED41F9C373FE6AFDCCAFBF0DA8C88D3D90D"
ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "app/src/main/assets"


def read_rom(path):
    path = Path(path)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n.lower().endswith((".sfc", ".smc"))]
            if len(names) != 1:
                raise ValueError("ROM ZIP must contain exactly one .sfc or .smc")
            data = archive.read(names[0])
    else:
        data = path.read_bytes()
    if len(data) % 32768 == 512:
        data = data[512:]
    return data


def crc(data):
    return zlib.crc32(data) & 0xFFFFFFFF


def encode_int(value):
    out = bytearray()
    while True:
        byte = value & 127
        value >>= 7
        if not value:
            out.append(byte | 128)
            return out
        out.append(byte)
        value -= 1


def apply_bps(source, patch):
    """Independent BPS reader, including TargetCopy used by the existing US patch."""
    if len(patch) < 19 or patch[:4] != b"BPS1":
        raise ValueError("Invalid BPS patch")
    source_crc, target_crc, patch_crc = struct.unpack_from("<III", patch, len(patch) - 12)
    if crc(source) != source_crc or crc(patch[:-4]) != patch_crc:
        raise ValueError("Source or patch checksum mismatch")
    pos, trailer = 4, len(patch) - 12

    def number():
        nonlocal pos
        value, shift = 0, 1
        while pos < trailer:
            byte = patch[pos]
            pos += 1
            value += (byte & 127) * shift
            if byte & 128:
                return value
            shift <<= 7
            value += shift
        raise ValueError("Truncated BPS integer")

    source_size, target_size, metadata_size = number(), number(), number()
    if source_size != len(source) or pos + metadata_size > trailer:
        raise ValueError("Invalid source or metadata size")
    pos += metadata_size
    target = bytearray()
    source_relative = target_relative = 0
    while pos < trailer:
        command = number()
        mode, size = command & 3, (command >> 2) + 1
        if len(target) + size > target_size:
            raise ValueError("BPS output overflow")
        if mode == 0:
            start = len(target)
            if start + size > len(source):
                raise ValueError("SourceRead out of range")
            target.extend(source[start:start + size])
        elif mode == 1:
            if pos + size > trailer:
                raise ValueError("TargetRead out of range")
            target.extend(patch[pos:pos + size])
            pos += size
        else:
            delta = number()
            delta = -(delta >> 1) if delta & 1 else delta >> 1
            if mode == 2:
                source_relative += delta
                if source_relative < 0 or source_relative + size > len(source):
                    raise ValueError("SourceCopy out of range")
                target.extend(source[source_relative:source_relative + size])
                source_relative += size
            else:
                target_relative += delta
                if target_relative < 0 or target_relative >= len(target):
                    raise ValueError("TargetCopy out of range")
                for _ in range(size):
                    target.append(target[target_relative])
                    target_relative += 1
    if len(target) != target_size or crc(target) != target_crc:
        raise ValueError("Target size or checksum mismatch")
    return bytes(target)


def create_bps(source, target):
    # The first occurrence gives deterministic matches and keeps the index small.
    # Continuations also try the previous SourceCopy end, preserving long runs
    # even when the same 16-byte pattern occurs elsewhere in the ROM.
    block = 16
    index = {}
    for p in range(len(source) - block + 1):
        index.setdefault(source[p:p + block], p)
    patch = bytearray(b"BPS1")
    metadata = b"zelda3-android PT-BR to baseline assets v1"
    for value in (len(source), len(target), len(metadata)):
        patch.extend(encode_int(value))
    patch.extend(metadata)
    pos = literal_start = relative = 0
    while pos < len(target):
        key = target[pos:pos + block]
        best_start, best_length = 0, 0
        candidates = [index.get(key, -1), relative]
        for start in candidates:
            if start < 0 or len(key) != block or source[start:start + block] != key:
                continue
            size = block
            limit = min(len(source) - start, len(target) - pos)
            while size < limit and source[start + size] == target[pos + size]:
                size += 1
            if size > best_length:
                best_start, best_length = start, size
        if best_length:
            if pos > literal_start:
                patch.extend(encode_int(((pos - literal_start - 1) << 2) | 1))
                patch.extend(target[literal_start:pos])
            patch.extend(encode_int(((best_length - 1) << 2) | 2))
            delta = best_start - relative
            patch.extend(encode_int((abs(delta) << 1) | (delta < 0)))
            relative = best_start + best_length
            pos += best_length
            literal_start = pos
        else:
            pos += 1
    if pos > literal_start:
        patch.extend(encode_int(((pos - literal_start - 1) << 2) | 1))
        patch.extend(target[literal_start:pos])
    patch.extend(struct.pack("<II", crc(source), crc(target)))
    patch.extend(struct.pack("<I", crc(patch)))
    return bytes(patch)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--us-rom", required=True, help="Original US .sfc/.smc or ZIP")
    parser.add_argument("--translated-rom", required=True, help="Known PT-BR .sfc/.smc or ZIP")
    parser.add_argument("--base-patch", type=Path, default=ASSETS / "zelda3_assets.bps")
    parser.add_argument("--output", type=Path, default=ASSETS / "zelda3_assets_ptbr.bps")
    args = parser.parse_args()
    us, translated = read_rom(args.us_rom), read_rom(args.translated_rom)
    for label, data, expected in (("US", us, US_SHA1), ("PT-BR", translated, PT_SHA1)):
        if hashlib.sha1(data).hexdigest().upper() != expected:
            parser.error(f"{label} ROM does not match expected SHA-1 {expected}")
    target = apply_bps(us, args.base_patch.read_bytes())
    patch = create_bps(translated, target)
    if apply_bps(translated, patch) != target:
        raise ValueError("Generated patch failed byte-for-byte verification")
    args.output.write_bytes(patch)
    print(f"Verified: {len(patch):,} byte BPS -> {len(target):,} byte baseline assets")
    print(f"BPS SHA-256: {hashlib.sha256(patch).hexdigest()}")
    print(f"Baseline SHA-256: {hashlib.sha256(target).hexdigest()}")


if __name__ == "__main__":
    main()
