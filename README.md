# CHRplunk NES IDE

A comprehensive Integrated Development Environment (IDE) for Nintendo Entertainment System (NES) game development, built as a native GNOME application. Features project management, 6502 assembly editing with syntax highlighting, build system integration, and CHR graphics editing.

![GNOME](https://img.shields.io/badge/GNOME-native-blue)
![GTK4](https://img.shields.io/badge/GTK-4-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)

## IDE Features

### Project Management
- **Project system**: Create and manage NES development projects with `.nesproject` configuration
- **Project templates**: Quick start with Empty, Hello World, and Platformer templates
- **File organization**: Automatic directory structure (source, graphics, audio, data, build)
- **Project sidebar**: Tree view of all project files

### Code Editor
- **6502 Assembly editing**: Full syntax highlighting for 6502 assembly language
- **GtkSourceView integration**: Professional code editing experience
- **Multiple tabs**: Work on multiple files simultaneously
- **Line numbers**: Easy code navigation
- **Monospace font**: Optimized for code reading

### Build System
- **ca65 support**: Integrated CC65 assembler and linker
- **asm6 support**: Alternative assembler support
- **Build configurations**: Debug and Release configurations
- **Build output panel**: See compiler messages in real-time
- **Error parsing**: Click errors to jump to source location
- **One-click builds**: F7 to build, F5 to build and run

### Multi-Panel Architecture
- **Sidebar**: Project file tree
- **Main editor**: Tabbed code editor
- **Bottom panel**: Build output, console, and problem list
- **Resizable panels**: Customize your workspace

## Graphics Editor Features

- **View CHR files**: Display all tiles in a CHR file as an organized grid
- **Open NES ROMs**: Extract and view CHR data directly from NES ROM files (.nes)
- **Multiple CHR banks**: Select which CHR bank to view when ROMs have multiple banks
- **Edit tiles**: Double-click any tile to open a detailed pixel editor
- **Paint mode**: Click and drag to paint individual pixels
- **Customizable color palette**: Edit the 4-color palette with a built-in color picker
- **Smart window sizing**: Window automatically resizes to fit the loaded CHR file
- **Save changes**: Save your edits back to CHR files
- **Native GNOME experience**: Built with GTK4 and libadwaita for a modern GNOME interface

## What are CHR files?

CHR files contain tile/character graphics data for NES (Nintendo Entertainment System) games. Each tile is 8x8 pixels with 2 bits per pixel (4 colors). These files are used in NES ROM development and emulation.

## NES ROM Support

CHRplunk can open NES ROM files (.nes) in iNES format and extract CHR data:

- **Automatic detection**: Simply open a .nes file and CHRplunk will parse it
- **Visual bank selector**: Multiple CHR banks are shown with tile previews for easy identification
- **ROM information**: View details about the ROM (mapper, PRG/CHR sizes, mirroring)
- **CHR RAM detection**: ROMs that use CHR RAM instead of CHR ROM are detected and reported

Note: CHRplunk is read-only for NES ROMs. To save changes, export the CHR data to a standalone .chr file.

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

### Create sample files for testing

```bash
# Create a standalone CHR file
python3 create_sample_chr.py sample.chr
./run.sh sample.chr

# Create a sample NES ROM with CHR data
python3 create_sample_rom.py sample.nes
./run.sh sample.nes
```

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions for various Linux distributions.

## Usage

1. **Open a file**: Click the folder icon in the header bar or use Ctrl+O
   - Open standalone CHR files (.chr)
   - Open NES ROM files (.nes) - select CHR bank if multiple banks exist
2. **View tiles**: All tiles are displayed in a grid (16 tiles per row by default)
3. **Customize colors**: Use the palette editor on the right to change any of the 4 colors
4. **Edit a tile**: Double-click any tile to open the tile editor
5. **Paint pixels**: In the tile editor, select a color and click/drag to paint
6. **Save changes**: Click the save icon or use Ctrl+S (CHR files only)

## Keyboard Shortcuts

### IDE Mode
- `F5` - Build and Run
- `F7` - Build Project
- `Ctrl+S` - Save current file
- `Ctrl+Shift+S` - Save all files
- `Ctrl+O` - Open file
- `Ctrl+,` - Preferences
- `Ctrl+Q` - Quit application

### Graphics Editor Mode
- `Ctrl+O` - Open CHR file or NES ROM
- `Ctrl+S` - Save current file
- `Ctrl+Shift+S` - Save as
- `Ctrl+Q` - Quit application

## Technical Details

- **Built with**: Python, GTK4, libadwaita
- **Supported formats**:
  - Standard NES CHR files (.chr)
  - NES ROM files in iNES format (.nes)
- **Tile format**: 8x8 pixels, 2 bits per pixel, 16 bytes per tile
- **CHR ROM parsing**: Supports multiple 8KB CHR banks, mapper detection, ROM info display

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
