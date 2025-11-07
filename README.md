# CHRplunk

A native GNOME application for editing NES CHR (Character/Tile Graphics) files.

![GNOME](https://img.shields.io/badge/GNOME-native-blue)
![GTK4](https://img.shields.io/badge/GTK-4-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)

## Features

- **View CHR files**: Display all tiles in a CHR file as an organized grid
- **Edit tiles**: Double-click any tile to open a detailed pixel editor
- **Paint mode**: Click and drag to paint individual pixels
- **Color palette**: Work with the standard NES 2-bit color palette
- **Save changes**: Save your edits back to CHR files
- **Native GNOME experience**: Built with GTK4 and libadwaita for a modern GNOME interface

## What are CHR files?

CHR files contain tile/character graphics data for NES (Nintendo Entertainment System) games. Each tile is 8x8 pixels with 2 bits per pixel (4 colors). These files are used in NES ROM development and emulation.

## Quick Start

### Running without installation

```bash
# Install dependencies (Debian/Ubuntu)
sudo apt install python3 python3-gi gir1.2-gtk-4.0 gir1.2-adwaita-1

# Run the application
./run.sh

# Or open a specific file
./run.sh /path/to/file.chr
```

### Create a sample CHR file for testing

```bash
python3 create_sample_chr.py sample.chr
./run.sh sample.chr
```

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions for various Linux distributions.

## Usage

1. **Open a CHR file**: Click the folder icon in the header bar or use Ctrl+O
2. **View tiles**: All tiles are displayed in a grid (16 tiles per row by default)
3. **Edit a tile**: Double-click any tile to open the tile editor
4. **Paint pixels**: In the tile editor, select a color and click/drag to paint
5. **Save changes**: Click the save icon or use Ctrl+S

## Keyboard Shortcuts

- `Ctrl+O` - Open CHR file
- `Ctrl+S` - Save current file
- `Ctrl+Shift+S` - Save as
- `Ctrl+Q` - Quit application

## Technical Details

- **Built with**: Python, GTK4, libadwaita
- **Supported formats**: Standard NES CHR files (.chr)
- **Tile format**: 8x8 pixels, 2 bits per pixel, 16 bytes per tile

## Development

```bash
git clone https://github.com/rosskarchner/CHRplunk.git
cd CHRplunk
pip3 install -r requirements.txt
./run.sh
```

## License

GPL-3.0+ (see LICENSE file)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
