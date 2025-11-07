"""Main window implementation"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib, GdkPixbuf, Gdk
from chrplunk.chr_format import CHRFile, NES_PALETTE
from chrplunk.tile_viewer import TileViewer
from chrplunk.palette_editor import PaletteEditor
from chrplunk.nes_rom import NESRom, NESRomError
from chrplunk.bank_selector import BankSelectorDialog, RomInfoDialog
import os

class MainWindow(Adw.ApplicationWindow):
    """Main application window"""

    def __init__(self, application):
        super().__init__(application=application)

        self.chr_file = None
        self.current_filepath = None
        self.current_palette = list(NES_PALETTE)  # Current palette (mutable copy)

        # Set up window
        self.set_title('CHRplunk')
        self.set_default_size(900, 700)

        # Create header bar
        header = Adw.HeaderBar()

        # Open button
        open_button = Gtk.Button(icon_name='document-open-symbolic')
        open_button.set_tooltip_text('Open CHR file')
        open_button.connect('clicked', lambda x: self.show_open_dialog())
        header.pack_start(open_button)

        # Save button
        save_button = Gtk.Button(icon_name='document-save-symbolic')
        save_button.set_tooltip_text('Save CHR file')
        save_button.connect('clicked', lambda x: self.save_file())
        header.pack_start(save_button)

        # Menu button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name('open-menu-symbolic')
        menu = Gio.Menu()
        menu.append('Save As...', 'app.save-as')
        menu.append('About CHRplunk', 'app.about')
        menu.append('Quit', 'app.quit')
        menu_button.set_menu_model(menu)
        header.pack_end(menu_button)

        # Create main content
        self.toolbox = Adw.ToolbarView()
        self.toolbox.add_top_bar(header)

        # Create scrolled window for tile viewer
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        # Create tile viewer
        self.tile_viewer = TileViewer()
        scrolled.set_child(self.tile_viewer)

        # Create palette editor
        self.palette_editor = PaletteEditor(self.current_palette)
        self.palette_editor.connect('palette-changed', self.on_palette_changed)

        # Create horizontal paned for tile viewer and palette
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_start_child(scrolled)
        paned.set_end_child(self.palette_editor)
        paned.set_shrink_start_child(False)
        paned.set_shrink_end_child(False)
        paned.set_resize_start_child(True)
        paned.set_resize_end_child(False)
        paned.set_position(600)  # Initial position

        # Create status page for empty state
        self.status_page = Adw.StatusPage(
            title='No CHR file loaded',
            description='Open a CHR file to view and edit NES graphics',
            icon_name='document-open-symbolic'
        )

        # Create stack to switch between empty state and viewer
        self.stack = Gtk.Stack()
        self.stack.add_named(self.status_page, 'empty')
        self.stack.add_named(paned, 'viewer')
        self.stack.set_visible_child_name('empty')

        self.toolbox.set_content(self.stack)
        self.set_content(self.toolbox)

        # Connect tile edit signal
        self.tile_viewer.connect('tile-edited', self.on_tile_edited)

    def show_open_dialog(self):
        """Show file open dialog"""
        dialog = Gtk.FileDialog()
        dialog.set_title('Open CHR File or NES ROM')

        # Create file filters
        filter_chr = Gtk.FileFilter()
        filter_chr.set_name('CHR files')
        filter_chr.add_pattern('*.chr')
        filter_chr.add_mime_type('application/x-nes-chr')

        filter_nes = Gtk.FileFilter()
        filter_nes.set_name('NES ROM files')
        filter_nes.add_pattern('*.nes')
        filter_nes.add_pattern('*.NES')
        filter_nes.add_mime_type('application/x-nes-rom')

        filter_all_supported = Gtk.FileFilter()
        filter_all_supported.set_name('All supported files')
        filter_all_supported.add_pattern('*.chr')
        filter_all_supported.add_pattern('*.nes')
        filter_all_supported.add_pattern('*.NES')

        filter_all = Gtk.FileFilter()
        filter_all.set_name('All files')
        filter_all.add_pattern('*')

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_all_supported)
        filters.append(filter_chr)
        filters.append(filter_nes)
        filters.append(filter_all)
        dialog.set_filters(filters)

        dialog.open(self, None, self.on_open_response)

    def on_open_response(self, dialog, result):
        """Handle file open dialog response"""
        try:
            file = dialog.open_finish(result)
            if file:
                self.open_file(file.get_path())
        except GLib.Error as e:
            if e.code != 2:  # Not a dismiss error
                print(f'Error opening file: {e.message}')

    def open_file(self, filepath: str):
        """Open a CHR file or NES ROM"""
        try:
            # Check file extension to determine type
            ext = os.path.splitext(filepath)[1].lower()

            if ext == '.nes':
                self.open_nes_rom(filepath)
            else:
                # Assume CHR file
                self.open_chr_file(filepath)

        except NESRomError as e:
            dialog = Adw.MessageDialog(
                transient_for=self,
                heading='Error opening NES ROM',
                body=str(e)
            )
            dialog.add_response('ok', 'OK')
            dialog.present()
        except Exception as e:
            dialog = Adw.MessageDialog(
                transient_for=self,
                heading='Error opening file',
                body=str(e)
            )
            dialog.add_response('ok', 'OK')
            dialog.present()

    def open_chr_file(self, filepath: str):
        """Open a standalone CHR file"""
        self.chr_file = CHRFile.from_file(filepath)
        self.current_filepath = filepath
        self.tile_viewer.set_chr_file(self.chr_file, self.current_palette)
        self.stack.set_visible_child_name('viewer')

        # Update window title
        filename = os.path.basename(filepath)
        self.set_title(f'{filename} - CHRplunk')

        # Resize window to fit content
        self.resize_to_content()

    def open_nes_rom(self, filepath: str):
        """Open a NES ROM file and extract CHR data"""
        rom = NESRom(filepath)

        if not rom.has_chr_rom():
            # Show info dialog for ROMs with CHR RAM
            info_dialog = RomInfoDialog(self, rom)
            info_dialog.present()
            return

        if rom.get_chr_bank_count() == 1:
            # Single CHR bank, open directly
            chr_data = rom.get_chr_bank(0)
            self.load_chr_data(chr_data, filepath, 0)
        else:
            # Multiple CHR banks, show selector
            selector = BankSelectorDialog(self, rom)
            selector.connect('bank-selected', lambda d, bank: self.load_chr_from_rom(filepath, bank))
            selector.present()

    def load_chr_from_rom(self, filepath: str, bank_index: int):
        """Load a specific CHR bank from a NES ROM"""
        try:
            rom = NESRom(filepath)
            chr_data = rom.get_chr_bank(bank_index)
            self.load_chr_data(chr_data, filepath, bank_index)
        except Exception as e:
            dialog = Adw.MessageDialog(
                transient_for=self,
                heading='Error loading CHR bank',
                body=str(e)
            )
            dialog.add_response('ok', 'OK')
            dialog.present()

    def load_chr_data(self, chr_data: bytes, source_filepath: str, bank_index: int = None):
        """Load CHR data from bytes"""
        self.chr_file = CHRFile.from_bytes(chr_data)
        self.current_filepath = source_filepath
        self.tile_viewer.set_chr_file(self.chr_file, self.current_palette)
        self.stack.set_visible_child_name('viewer')

        # Update window title
        filename = os.path.basename(source_filepath)
        if bank_index is not None:
            self.set_title(f'{filename} [Bank {bank_index}] - CHRplunk')
        else:
            self.set_title(f'{filename} - CHRplunk')

        # Resize window to fit content
        self.resize_to_content()

    def resize_to_content(self):
        """Resize window to fit the loaded CHR file content"""
        if not self.chr_file:
            return

        # Calculate content size
        tile_size = self.tile_viewer.tile_size
        tiles_per_row = self.tile_viewer.tiles_per_row
        rows = (self.chr_file.tile_count + tiles_per_row - 1) // tiles_per_row

        # Calculate ideal window size
        content_width = tiles_per_row * tile_size
        content_height = rows * tile_size

        # Add palette editor width and some padding
        palette_width = 250
        total_width = content_width + palette_width + 40

        # Add header bar height and padding
        total_height = content_height + 100

        # Clamp to reasonable min/max sizes
        total_width = max(600, min(total_width, 1400))
        total_height = max(400, min(total_height, 1000))

        self.set_default_size(total_width, total_height)

    def save_file(self):
        """Save the current file"""
        if not self.chr_file:
            return

        if self.current_filepath:
            try:
                self.chr_file.save(self.current_filepath)
                self.show_toast('File saved successfully')
            except Exception as e:
                dialog = Adw.MessageDialog(
                    transient_for=self,
                    heading='Error saving file',
                    body=str(e)
                )
                dialog.add_response('ok', 'OK')
                dialog.present()
        else:
            self.show_save_dialog()

    def show_save_dialog(self):
        """Show file save dialog"""
        if not self.chr_file:
            return

        dialog = Gtk.FileDialog()
        dialog.set_title('Save CHR File')

        # Create file filter
        filter_chr = Gtk.FileFilter()
        filter_chr.set_name('CHR files')
        filter_chr.add_pattern('*.chr')

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_chr)
        dialog.set_filters(filters)

        if self.current_filepath:
            import os
            dialog.set_initial_name(os.path.basename(self.current_filepath))

        dialog.save(self, None, self.on_save_response)

    def on_save_response(self, dialog, result):
        """Handle file save dialog response"""
        try:
            file = dialog.save_finish(result)
            if file:
                filepath = file.get_path()
                self.chr_file.save(filepath)
                self.current_filepath = filepath
                self.show_toast('File saved successfully')

                # Update window title
                import os
                filename = os.path.basename(filepath)
                self.set_title(f'{filename} - CHRplunk')

        except GLib.Error as e:
            if e.code != 2:  # Not a dismiss error
                dialog = Adw.MessageDialog(
                    transient_for=self,
                    heading='Error saving file',
                    body=e.message
                )
                dialog.add_response('ok', 'OK')
                dialog.present()

    def show_toast(self, message: str):
        """Show a toast notification"""
        toast = Adw.Toast(title=message)
        toast.set_timeout(2)

        # Get or create toast overlay
        if not hasattr(self, 'toast_overlay'):
            self.toast_overlay = Adw.ToastOverlay()
            self.toast_overlay.set_child(self.stack)
            self.toolbox.set_content(self.toast_overlay)

        self.toast_overlay.add_toast(toast)

    def on_tile_edited(self, viewer, tile_index, tile_data):
        """Handle tile edit event"""
        if self.chr_file:
            self.chr_file.set_tile(tile_index, tile_data)

    def on_palette_changed(self, palette_editor, new_palette):
        """Handle palette change event"""
        self.current_palette = new_palette
        if self.chr_file:
            self.tile_viewer.set_palette(new_palette)
