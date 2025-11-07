"""Main application class"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib
from chrplunk.window import MainWindow

class Application(Adw.Application):
    """Main application class"""

    def __init__(self):
        super().__init__(
            application_id='com.github.chrplunk',
            flags=Gio.ApplicationFlags.HANDLES_OPEN
        )
        self.window = None

        # Create actions
        self.create_action('quit', self.on_quit_action, ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('open', self.on_open_action, ['<primary>o'])
        self.create_action('save', self.on_save_action, ['<primary>s'])
        self.create_action('save-as', self.on_save_as_action, ['<primary><shift>s'])

    def do_activate(self):
        """Called when the application is activated"""
        if not self.window:
            self.window = MainWindow(application=self)
        self.window.present()

    def do_open(self, files, n_files, hint):
        """Called when files are opened with the application"""
        self.do_activate()
        if len(files) > 0:
            self.window.open_file(files[0].get_path())

    def create_action(self, name, callback, shortcuts=None):
        """Create a Gio.SimpleAction"""
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f'app.{name}', shortcuts)

    def on_quit_action(self, action, param):
        """Quit the application"""
        self.quit()

    def on_about_action(self, action, param):
        """Show the about dialog"""
        about = Adw.AboutWindow(
            transient_for=self.window,
            application_name='CHRplunk',
            application_icon='com.github.chrplunk',
            developer_name='CHRplunk Contributors',
            version='0.1.0',
            website='https://github.com/rosskarchner/CHRplunk',
            issue_url='https://github.com/rosskarchner/CHRplunk/issues',
            copyright='© 2025 CHRplunk Contributors',
            license_type=Gtk.License.GPL_3_0,
            developers=['CHRplunk Contributors'],
            designers=['CHRplunk Contributors'],
        )
        about.present()

    def on_open_action(self, action, param):
        """Open file dialog"""
        if self.window:
            self.window.show_open_dialog()

    def on_save_action(self, action, param):
        """Save current file"""
        if self.window:
            self.window.save_file()

    def on_save_as_action(self, action, param):
        """Save as dialog"""
        if self.window:
            self.window.show_save_dialog()
