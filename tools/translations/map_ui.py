#!/usr/bin/env python3
"""Map the supported PT-BR ROM's interface, emitting metadata only (no ROM data).

The pointer layouts and compression commands follow snesrev/zelda3's
assets/tables.py, compile_resources.py and util.py. Offsets below are file
offsets, after removing a copier header. See ptbr_ui_manifest.json.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib

from build_ptbr_patch import ROOT, US_SHA1, PT_SHA1, read_rom

SOURCES = ['hud.c', 'select_file.c', 'attract.c', 'messaging.c', 'ending.c']


def lorom(addr):
    if not addr & 0x8000:
        raise ValueError('Not a LoROM address')
    return ((addr >> 16) & 127) * 32768 + (addr & 32767)


def decompress(rom, offset):
    start, out = offset, bytearray()
    def byte():
        nonlocal offset
        if offset >= len(rom) or offset - start >= 16384:
            raise ValueError('Truncated graphics')
        v = rom[offset]
        offset += 1
        return v
    while True:
        c = byte()
        if c == 255:
            return bytes(out), offset - start
        if c & 0xe0 == 0xe0:
            n, cmd = (((c & 3) << 8) | byte()) + 1, (c << 3) & 0xe0
        else:
            n, cmd = (c & 31) + 1, c & 0xe0
        if len(out) + n > 4096:
            raise ValueError('Oversized graphics')
        if cmd == 0:
            out.extend(byte() for _ in range(n))
        elif cmd & 128:
            p = byte() | byte() << 8
            for _ in range(n):
                if p >= len(out):
                    raise ValueError('Invalid graphics copy')
                out.append(out[p])
                p += 1
        elif cmd == 32:
            out.extend(bytes([byte()]) * n)
        elif cmd == 64:
            a, b = byte(), byte()
            out.extend((a, b)[i & 1] for i in range(n))
        elif cmd == 96:
            a = byte()
            out.extend((a + i) & 255 for i in range(n))
        else:
            raise ValueError('Unknown graphics command')


def stripe_size(rom, p):
    start = p
    while p < len(rom) and not rom[p] & 128:
        if p + 4 > len(rom):
            raise ValueError('Truncated stripe header')
        n = ((rom[p + 2] << 8 | rom[p + 3]) & 0x3fff) + 1
        if n & 1 and not rom[p + 2] & 64:
            raise ValueError('Odd stripe size')
        p += 4 + (2 if rom[p + 2] & 64 else n)
        if p - start > 16384:
            raise ValueError('Oversized stripe')
    if p >= len(rom):
        raise ValueError('Truncated stripe')
    return p - start + 1


def arrays():
    for file in SOURCES:
        text = (ROOT / 'app/jni/src/src' / file).read_text()
        pattern = r'(?:static )?const (u?int(?:8|16)) (\w+)\[[^;=]*=\s*\{(.*?)\};'
        for m in re.finditer(pattern, text, re.S):
            typ, name, body = m.groups()
            if name.endswith('_US'):
                name = name[:-3]
            body = re.sub(r'//[^\n]*', '', body).replace('{', '').replace('}', '')
            try:
                ns = [int(x.strip(), 0) for x in body.split(',') if x.strip()]
            except ValueError:
                continue
            width = 1 if '8' in typ else 2
            data = b''.join((v & ((1 << (width * 8)) - 1)).to_bytes(width, 'little') for v in ns)
            if len(data) >= 8:
                yield file, name, data


def map_roms(us, pt):
    if hashlib.sha1(us).hexdigest().upper() != US_SHA1 or hashlib.sha1(pt).hexdigest().upper() != PT_SHA1:
        raise ValueError('Unsupported ROM checksum')
    entries, audit = [], []
    def add(id, kind, index, name, off, size, base, decoded=None, source=None):
        data = pt[off:off + size]
        if len(data) != size:
            raise ValueError('Resource outside ROM')
        entry = dict(id=id, kind=kind, index=index, name=name, offset=off, size=size,
                     sha256=hashlib.sha256(data).hexdigest(),
                     original_sha256=hashlib.sha256(base).hexdigest())
        if decoded is not None:
            entry['decoded_size'] = len(decoded)
            entry['decoded_sha256'] = hashlib.sha256(decoded).hexdigest()
        if source:
            entry['source'] = source
        entries.append(entry)
    for file, name, data in arrays():
        off = us.find(data)
        # Attract arrays include the next stripe's leading byte; search through
        # their own terminator when the final padding does not match.
        if off < 0 and name.startswith('kAttract_Legendgraphics_'):
            off = us.find(data[:-1])
        if off < 0:
            continue
        changed = pt[off:off + len(data)] != data
        audit.append(dict(source=file, name=name, offset=off, size=len(data), changed=changed))
        if changed:
            # Only text/stripe tables changed in the supported hack. Never
            # import unrelated movement, physics, damage or animation tables.
            if file not in ['hud.c', 'select_file.c']:
                raise ValueError('Unexpected changed table: ' + name)
            add(len(entries) + 1, 'table', 0, name, off, len(data), data, source=file)
    for kind, count, lo, hi, bank, first in [
            ('sprite', 108, 0x51b1, 0x50d2, 0x4ff3, 0x100),
            ('background', 115, 0x513e, 0x505f, 0x4f80, 0x200)]:
        for i in range(count):
            blocks = []
            for rom in (us, pt):
                off = lorom(rom[lo+i] | rom[hi+i] << 8 | rom[bank+i] << 16)
                if kind == 'sprite' and i < 12:
                    dec, size = rom[off:off+1536], 1536
                else:
                    dec, size = decompress(rom, off)
                blocks.append((off, size, dec))
            a, b = blocks
            if a[2] != b[2]:
                add(first+i, kind, i, f'{kind}_{i:02x}', b[0], b[1],
                    us[a[0]:a[0]+a[1]], b[2])
    for i, addr in enumerate([0xcdd6d, 0xce7bf, 0xce2a8, 0xce63c, 0xce456, 0xeda9c]):
        off = lorom(addr)
        a, b = stripe_size(us, off), stripe_size(pt, off)
        audit.append(dict(name=f'kBgTilemap_{i}', offset=off, size=b,
                          changed=us[off:off+a] != pt[off:off+b]))
        if us[off:off+a] != pt[off:off+b]:
            add(0x300+99+i, 'asset', 99+i, f'kBgTilemap_{i}', off, b, us[off:off+a])
    # PT credits no longer use US byte indices into kEnding_MapData. Each row
    # stores one shared palette/attribute byte followed by its tile bytes.
    # Scene captions are relocated to $A0:80C8 and use the same row encoding.
    offsets = struct.unpack_from('<394H', pt, 0x7393d)
    extent = max(o + (1 if pt[0x73038+o] == 255 else 3 + (pt[0x73038+o+1]+1)//2) for o in offsets)
    add(0x400, 'font', 0, 'InterfaceFont', 0x70000, 4096, us[0x70000:0x71000])
    add(0x401, 'credits', 0, 'CreditsText', 0x73038, extent, us[0x73178:0x7393d])
    add(0x402, 'credits', 1, 'CreditsOffsets', 0x7393d, 788, us[0x7393d:0x73c51])
    end_size = struct.unpack_from('<H', pt, 0x742e1+32)[0]
    add(0x403, 'credits', 2, 'SceneCaptions', 0x1000c8, end_size, us[0x73f4c:0x742e1])
    add(0x404, 'credits', 3, 'SceneOffsets', 0x742e1, 34, us[0x742e1:0x74303])
    add(0x405, 'font', 1, 'NameFontMap', 0x77c09, 363, us[0x77c09:0x77c09+363])
    add(0x406, 'gameover', 0, 'GameOverCharacters', 0x100041, 36, us[0x475b4:0x475c4])
    add(0x407, 'gameover', 1, 'GameOverSweep', 0x475b4, 9, us[0x474ee:0x474f6])
    add(0x408, 'gameover', 2, 'GameOverUnfurl', 0x100065, 9, us[0x47565:0x4756d])
    manifest = dict(version=1, rom_sha1=PT_SHA1, original_sha1=US_SHA1,
                    entries=sorted(entries, key=lambda x:x['id']), audit=audit)
    package = build_package(pt, manifest)
    manifest['package_size'] = len(package)
    manifest['package_crc32'] = struct.unpack_from('<I', package, len(package)-4)[0]
    return manifest


def build_package(rom, manifest):
    entries = manifest['entries']
    out = bytearray(b'Z3UIBR01' + struct.pack('<II', 1, len(entries))
                    + bytes.fromhex(manifest['rom_sha1']) + bytes(4+12*len(entries)))
    for i, entry in enumerate(entries):
        out.extend(bytes((-len(out)) & 3))
        data = rom[entry['offset']:entry['offset']+entry['size']]
        if hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError('Unexpected resource: ' + entry['name'])
        struct.pack_into('<III', out, 40+i*12, entry['id'], len(out), len(data))
        out.extend(data)
    struct.pack_into('<I', out, 36, len(out)+4)
    out.extend(struct.pack('<I', zlib.crc32(out) & 0xffffffff))
    return bytes(out)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--us-rom', required=True)
    p.add_argument('--translated-rom', required=True)
    p.add_argument('--output', default=str(Path(__file__).with_name('ptbr_ui_manifest.json')))
    args = p.parse_args()
    manifest = map_roms(read_rom(args.us_rom), read_rom(args.translated_rom))
    Path(args.output).write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f"Mapped {len(manifest['entries'])} resources; audited {len(manifest['audit'])} tables")


if __name__ == '__main__':
    main()
