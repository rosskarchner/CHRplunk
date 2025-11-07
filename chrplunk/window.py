"""Main window implementation"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib, GdkPixbuf, Gdk
from chrplunk.chr_format import CHRFile
from chrplunk.tile_viewer import TileViewer

class MainWindow(Adw.ApplicationWindow):
    """Main application window"""

    def __init__(self, application):
        super().__init__(application=application)

        self.chr_file = None
        self.current_filepath = None

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

        # Create status page for empty state
        self.status_page = Adw.StatusPage(
            title='No CHR file loaded',
            description='Open a CHR file to view and edit NES graphics',
            icon_name='document-open-symbolic'
        )

        # Create stack to switch between empty state and viewer
        self.stack = Gtk.Stack()
        self.stack.add_named(self.status_page, 'empty')
        self.stack.add_named(scrolled, 'viewer')
        self.stack.set_visible_child_name('empty')

        self.toolbox.set_content(self.stack)
        self.set_content(self.toolbox)

        # Connect tile edit signal
        self.tile_viewer.connect('tile-edited', self.on_tile_edited)

    def show_open_dialog(self):
        """Show file open dialog"""
        dialog = Gtk.FileDialog()
        dialog.set_title('Open CHR File')

        # Create file filter
        filter_chr = Gtk.FileFilter()
        filter_chr.set_name('CHR files')
        filter_chr.add_pattern('*.chr')
        filter_chr.add_mime_type('application/x-nes-chr')

        filter_all = Gtk.FileFilter()
        filter_all.set_name('All files')
        filter_all.add_pattern('*')

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_chr)
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
        """Open a CHR file"""
        try:
            self.chr_file = CHRFile.from_file(filepath)
            self.current_filepath = filepath
            self.tile_viewer.set_chr_file(self.chr_file)
            self.stack.set_visible_child_name('viewer')

            # Update window title
            import os
            filename = os.path.basename(filepath)
            self.set_title(f'{filename} - CHRplunk')

        except Exception as e:
            dialog = Adw.MessageDialog(
                transient_for=self,
                heading='Error opening file',
                body=str(e)
            )
            dialog.add_response('ok', 'OK')
            dialog.present()

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
