"""CHR file format handler for NES graphics files"""

import io
from typing import List, Tuple
from gi.repository import GdkPixbuf, GLib

# NES 2C02 palette (simplified, first 4 colors for demo)
NES_PALETTE = [
    (84, 84, 84),      # Dark gray
    (0, 30, 116),      # Dark blue
    (8, 16, 144),      # Purple
    (48, 0, 136),      # Dark purple
]

class CHRFile:
    """Handles NES CHR file format

    CHR files contain 8x8 pixel tiles with 2 bits per pixel (4 colors).
    Each tile is 16 bytes: first 8 bytes are low bit plane, next 8 are high bit plane.
    """

    def __init__(self, data: bytes = None):
        self.data = bytearray(data) if data else bytearray()
        self.tile_count = len(self.data) // 16

    @classmethod
    def from_file(cls, filepath: str) -> 'CHRFile':
        """Load CHR file from disk"""
        with open(filepath, 'rb') as f:
            data = f.read()
        return cls(data)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'CHRFile':
        """Create CHR file from raw bytes"""
        return cls(data)

    def save(self, filepath: str):
        """Save CHR file to disk"""
        with open(filepath, 'wb') as f:
            f.write(self.data)

    def get_tile(self, tile_index: int) -> List[List[int]]:
        """Extract a single 8x8 tile as a 2D array of color indices (0-3)"""
        if tile_index >= self.tile_count:
            return [[0] * 8 for _ in range(8)]

        offset = tile_index * 16
        tile = [[0] * 8 for _ in range(8)]

        for y in range(8):
            low_byte = self.data[offset + y]
            high_byte = self.data[offset + y + 8]

            for x in range(8):
                bit = 7 - x
                low_bit = (low_byte >> bit) & 1
                high_bit = (high_byte >> bit) & 1
                color_index = (high_bit << 1) | low_bit
                tile[y][x] = color_index

        return tile

    def set_tile(self, tile_index: int, tile_data: List[List[int]]):
        """Set a tile from a 2D array of color indices (0-3)"""
        if tile_index >= self.tile_count:
            # Extend the data if needed
            self.data.extend([0] * ((tile_index + 1) * 16 - len(self.data)))
            self.tile_count = len(self.data) // 16

        offset = tile_index * 16

        for y in range(8):
            low_byte = 0
            high_byte = 0

            for x in range(8):
                bit = 7 - x
                color_index = tile_data[y][x]
                low_bit = color_index & 1
                high_bit = (color_index >> 1) & 1

                low_byte |= (low_bit << bit)
                high_byte |= (high_bit << bit)

            self.data[offset + y] = low_byte
            self.data[offset + y + 8] = high_byte

    def render_tile_to_pixbuf(self, tile_index: int, scale: int = 4,
                              palette: List[Tuple[int, int, int]] = None) -> GdkPixbuf.Pixbuf:
        """Render a tile to a GdkPixbuf with scaling"""
        if palette is None:
            palette = NES_PALETTE

        tile = self.get_tile(tile_index)
        width = 8 * scale
        height = 8 * scale

        # Create pixel data (RGB)
        pixels = []
        for y in range(8):
            for _ in range(scale):  # Scale vertically
                for x in range(8):
                    color_idx = tile[y][x]
                    color = palette[color_idx % len(palette)]
                    for _ in range(scale):  # Scale horizontally
                        pixels.extend(color)

        pixel_bytes = bytes(pixels)

        return GdkPixbuf.Pixbuf.new_from_bytes(
            GLib.Bytes.new(pixel_bytes),
            GdkPixbuf.Colorspace.RGB,
            False,  # has_alpha
            8,      # bits_per_sample
            width,
            height,
            width * 3  # rowstride
        )

    def render_all_tiles_to_pixbuf(self, tiles_per_row: int = 16, scale: int = 2,
                                   palette: List[Tuple[int, int, int]] = None) -> GdkPixbuf.Pixbuf:
        """Render all tiles to a single image"""
        if palette is None:
            palette = NES_PALETTE

        if self.tile_count == 0:
            # Return a small blank pixbuf
            return GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 64, 64)

        rows = (self.tile_count + tiles_per_row - 1) // tiles_per_row
        tile_size = 8 * scale
        width = tiles_per_row * tile_size
        height = rows * tile_size

        # Create pixel data
        pixels = bytearray(width * height * 3)

        for tile_idx in range(self.tile_count):
            tile = self.get_tile(tile_idx)
            tile_row = tile_idx // tiles_per_row
            tile_col = tile_idx % tiles_per_row

            for y in range(8):
                for sy in range(scale):
                    for x in range(8):
                        color_idx = tile[y][x]
                        color = palette[color_idx % len(palette)]

                        for sx in range(scale):
                            px = tile_col * tile_size + x * scale + sx
                            py = tile_row * tile_size + y * scale + sy
                            offset = (py * width + px) * 3

                            if offset + 2 < len(pixels):
                                pixels[offset:offset+3] = color

        return GdkPixbuf.Pixbuf.new_from_bytes(
            GLib.Bytes.new(bytes(pixels)),
            GdkPixbuf.Colorspace.RGB,
            False,
            8,
            width,
            height,
            width * 3
        )
