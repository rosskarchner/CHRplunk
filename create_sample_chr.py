#!/usr/bin/env python3
"""Create a sample CHR file for testing CHRplunk"""

import sys

def create_sample_chr(filename='sample.chr'):
    """Create a sample CHR file with some test patterns"""

    # Create 256 tiles (4KB - standard size for one CHR bank)
    data = bytearray()

    # Create some interesting patterns
    patterns = []

    # Pattern 1: Solid colors
    for color in range(4):
        tile = bytearray(16)
        if color & 1:
            tile[0:8] = [0xFF] * 8
        if color & 2:
            tile[8:16] = [0xFF] * 8
        patterns.append(tile)

    # Pattern 2: Checkerboard
    checkerboard = bytearray(16)
    checkerboard[0:8] = [0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55]
    checkerboard[8:16] = [0x00] * 8
    patterns.append(checkerboard)

    # Pattern 3: Vertical lines
    vlines = bytearray(16)
    vlines[0:8] = [0xFF] * 8
    vlines[8:16] = [0x00] * 8
    patterns.append(vlines)

    # Pattern 4: Horizontal lines
    hlines = bytearray(16)
    hlines[0:8] = [0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00]
    hlines[8:16] = [0x00] * 8
    patterns.append(hlines)

    # Pattern 5: Border
    border = bytearray(16)
    border[0:8] = [0xFF, 0x81, 0x81, 0x81, 0x81, 0x81, 0x81, 0xFF]
    border[8:16] = [0x00] * 8
    patterns.append(border)

    # Pattern 6: X pattern
    xpattern = bytearray(16)
    xpattern[0:8] = [0x81, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x81]
    xpattern[8:16] = [0x00] * 8
    patterns.append(xpattern)

    # Pattern 7: Diagonal
    diagonal = bytearray(16)
    diagonal[0:8] = [0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01]
    diagonal[8:16] = [0x00] * 8
    patterns.append(diagonal)

    # Pattern 8: Circle
    circle = bytearray(16)
    circle[0:8] = [0x3C, 0x42, 0x81, 0x81, 0x81, 0x81, 0x42, 0x3C]
    circle[8:16] = [0x00] * 8
    patterns.append(circle)

    # Fill first 32 tiles with patterns, repeat
    for i in range(256):
        pattern_idx = i % len(patterns)
        data.extend(patterns[pattern_idx])

    # Write to file
    with open(filename, 'wb') as f:
        f.write(data)

    print(f'Created sample CHR file: {filename}')
    print(f'Size: {len(data)} bytes ({len(data) // 16} tiles)')

if __name__ == '__main__':
    filename = sys.argv[1] if len(sys.argv) > 1 else 'sample.chr'
    create_sample_chr(filename)
