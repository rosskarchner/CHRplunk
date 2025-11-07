#!/usr/bin/env python3
"""Create a sample NES ROM for testing CHRplunk"""

import sys

def create_sample_nes_rom(filename='sample.nes'):
    """Create a minimal NES ROM with CHR data"""

    # iNES header (16 bytes)
    header = bytearray(16)
    header[0:4] = b'NES\x1a'  # Magic number
    header[4] = 1   # 1 PRG ROM bank (16 KB)
    header[5] = 2   # 2 CHR ROM banks (16 KB total)
    header[6] = 0   # Flags 6: Horizontal mirroring, mapper 0
    header[7] = 0   # Flags 7
    # Rest of header is zeros

    # PRG ROM (16 KB) - filled with simple pattern
    prg_rom = bytearray(16384)
    for i in range(len(prg_rom)):
        prg_rom[i] = i % 256

    # CHR ROM Bank 0 (8 KB) - patterns from our sample CHR creator
    chr_bank_0 = bytearray()

    # Create some test patterns for bank 0
    patterns_0 = []

    # Pattern 1: Solid colors
    for color in range(4):
        tile = bytearray(16)
        if color & 1:
            tile[0:8] = [0xFF] * 8
        if color & 2:
            tile[8:16] = [0xFF] * 8
        patterns_0.append(tile)

    # Pattern 2: Checkerboard
    checkerboard = bytearray(16)
    checkerboard[0:8] = [0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55]
    checkerboard[8:16] = [0x00] * 8
    patterns_0.append(checkerboard)

    # Pattern 3: Border
    border = bytearray(16)
    border[0:8] = [0xFF, 0x81, 0x81, 0x81, 0x81, 0x81, 0x81, 0xFF]
    border[8:16] = [0x00] * 8
    patterns_0.append(border)

    # Fill bank 0 with patterns
    for i in range(512):  # 512 tiles per 8KB bank
        pattern_idx = i % len(patterns_0)
        chr_bank_0.extend(patterns_0[pattern_idx])

    # CHR ROM Bank 1 (8 KB) - different patterns
    chr_bank_1 = bytearray()

    patterns_1 = []

    # Pattern 1: X pattern
    xpattern = bytearray(16)
    xpattern[0:8] = [0x81, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x81]
    xpattern[8:16] = [0x00] * 8
    patterns_1.append(xpattern)

    # Pattern 2: Diagonal
    diagonal = bytearray(16)
    diagonal[0:8] = [0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01]
    diagonal[8:16] = [0x00] * 8
    patterns_1.append(diagonal)

    # Pattern 3: Circle
    circle = bytearray(16)
    circle[0:8] = [0x3C, 0x42, 0x81, 0x81, 0x81, 0x81, 0x42, 0x3C]
    circle[8:16] = [0x00] * 8
    patterns_1.append(circle)

    # Pattern 4: Vertical lines
    vlines = bytearray(16)
    vlines[0:8] = [0xFF] * 8
    vlines[8:16] = [0x00] * 8
    patterns_1.append(vlines)

    # Fill bank 1 with patterns
    for i in range(512):
        pattern_idx = i % len(patterns_1)
        chr_bank_1.extend(patterns_1[pattern_idx])

    # Write ROM file
    with open(filename, 'wb') as f:
        f.write(header)
        f.write(prg_rom)
        f.write(chr_bank_0)
        f.write(chr_bank_1)

    print(f'Created sample NES ROM: {filename}')
    print(f'  Header: 16 bytes')
    print(f'  PRG ROM: 1 bank (16 KB)')
    print(f'  CHR ROM: 2 banks (16 KB total)')
    print(f'  Total size: {16 + len(prg_rom) + len(chr_bank_0) + len(chr_bank_1)} bytes')

if __name__ == '__main__':
    filename = sys.argv[1] if len(sys.argv) > 1 else 'sample.nes'
    create_sample_nes_rom(filename)
