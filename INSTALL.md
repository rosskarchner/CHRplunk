# Installation Guide for CHRplunk

CHRplunk is a native GNOME application for editing NES CHR (Character/Graphics) files.

## Requirements

- Python 3.8 or later
- GTK 4
- libadwaita 1.0 or later
- PyGObject (Python GObject Introspection bindings)

## Installation on Linux

### Debian/Ubuntu

```bash
# Install system dependencies
sudo apt install python3 python3-pip python3-gi python3-gi-cairo \
                 gir1.2-gtk-4.0 gir1.2-adwaita-1 meson

# Install Python dependencies
pip3 install -r requirements.txt

# Option 1: Run without installing
chmod +x run.sh
./run.sh

# Option 2: Build and install with meson
meson setup build
meson compile -C build
sudo meson install -C build
```

### Fedora

```bash
# Install system dependencies
sudo dnf install python3 python3-pip python3-gobject gtk4 libadwaita meson

# Install Python dependencies
pip3 install -r requirements.txt

# Option 1: Run without installing
chmod +x run.sh
./run.sh

# Option 2: Build and install with meson
meson setup build
meson compile -C build
sudo meson install -C build
```

### Arch Linux

```bash
# Install system dependencies
sudo pacman -S python python-pip python-gobject gtk4 libadwaita meson

# Install Python dependencies
pip3 install -r requirements.txt

# Option 1: Run without installing
chmod +x run.sh
./run.sh

# Option 2: Build and install with meson
meson setup build
meson compile -C build
sudo meson install -C build
```

## Quick Start

The easiest way to run CHRplunk without installing:

```bash
chmod +x run.sh
./run.sh
```

Or directly with Python:

```bash
python3 chrplunk-app.py
```

## Opening CHR Files

You can open CHR files in several ways:

1. **From the application**: Click the "Open" button in the header bar
2. **From command line**: `./run.sh /path/to/file.chr`
3. **Drag and drop**: Drag a .chr file onto the application window

## Features

- **View CHR tiles**: Display all tiles in a CHR file as a grid
- **Edit tiles**: Double-click any tile to open the tile editor
- **Paint pixels**: Click and drag to paint individual pixels
- **Color palette**: Select from the 4 available colors per tile
- **Save changes**: Save your edits back to the CHR file

## CHR File Format

CHR files contain 8x8 pixel tiles used in NES games. Each tile uses 2 bits per pixel (4 colors) and is stored as 16 bytes. CHRplunk supports standard CHR files used in NES development.

## Troubleshooting

### "No module named 'gi'"

Install PyGObject:
```bash
pip3 install PyGObject
```

### "Namespace Gtk not available"

Install GTK 4 development files:
```bash
# Debian/Ubuntu
sudo apt install gir1.2-gtk-4.0

# Fedora
sudo dnf install gtk4

# Arch
sudo pacman -S gtk4
```

### "Namespace Adw not available"

Install libadwaita:
```bash
# Debian/Ubuntu
sudo apt install gir1.2-adwaita-1

# Fedora
sudo dnf install libadwaita

# Arch
sudo pacman -S libadwaita
```

## Development

To contribute to CHRplunk:

```bash
# Clone the repository
git clone https://github.com/rosskarchner/CHRplunk.git
cd CHRplunk

# Install dependencies
pip3 install -r requirements.txt

# Run the application
./run.sh
```

## License

See LICENSE file for details.
