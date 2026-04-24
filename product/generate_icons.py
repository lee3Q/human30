#!/usr/bin/env python3
"""SVG → PNG 변환 없이, 최소 유효 PNG 생성 (placeholder).
실제 아이콘은 SVG가 메인. PNG는 PWA 필수 요구사항 충족용."""

import struct
import zlib
import os

def create_png(width, height, r, g, b):
    """단색 PNG 생성 (stdlib only)"""
    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = make_chunk(b'IHDR', ihdr_data)

    # IDAT (raw pixels)
    raw = b''
    for y in range(height):
        raw += b'\x00'  # filter: none
        for x in range(width):
            # 간단한 원형 그라데이션
            cx, cy = width // 2, height // 2
            dx, dy = x - cx, y - cy
            dist = (dx * dx + dy * dy) ** 0.5
            max_dist = min(width, height) * 0.4
            if dist < max_dist:
                raw += bytes([r, g, b])
            else:
                raw += bytes([10, 10, 10])  # 배경 #0a0a0a

    compressed = zlib.compress(raw)
    idat = make_chunk(b'IDAT', compressed)

    # IEND
    iend = make_chunk(b'IEND', b'')

    # PNG signature + chunks
    return b'\x89PNG\r\n\x1a\n' + ihdr + idat + iend

def make_chunk(chunk_type, data):
    chunk = chunk_type + data
    crc = zlib.crc32(chunk) & 0xffffffff
    return struct.pack('>I', len(data)) + chunk + struct.pack('>I', crc)

if __name__ == '__main__':
    d = os.path.dirname(os.path.abspath(__file__))

    # 192x192
    png192 = create_png(192, 192, 200, 162, 255)  # #c8a2ff
    with open(os.path.join(d, 'icon-192.png'), 'wb') as f:
        f.write(png192)
    print(f'icon-192.png: {len(png192)} bytes')

    # 512x512
    png512 = create_png(512, 512, 200, 162, 255)
    with open(os.path.join(d, 'icon-512.png'), 'wb') as f:
        f.write(png512)
    print(f'icon-512.png: {len(png512)} bytes')

    print('done')
