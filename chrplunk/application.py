"""Main application class"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib
from chrplunk.window import MainWindow
from chrplunk.ide_window import IDEWindow

class Application(Adw.Application):
    """Main application class"""

    def __init__(self, use_ide_mode=True):
        super().__init__(
            application_id='com.github.chrplunk',
            flags=Gio.ApplicationFlags.HANDLES_OPEN
        )
        self.window = None
        self.use_ide_mode = use_ide_mode

        # Create actions
        self.create_action('quit', self.on_quit_action, ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('open', self.on_open_action, ['<primary>o'])
        self.create_action('save', self.on_save_action, ['<primary>s'])
        self.create_action('save-as', self.on_save_as_action, ['<primary><shift>s'])

        # IDE-specific actions
        self.create_action('new-project', self.on_new_project_action)
        self.create_action('open-project', self.on_open_project_action)
        self.create_action('close-project', self.on_close_project_action)
        self.create_action('build', self.on_build_action, ['F7'])
        self.create_action('run', self.on_run_action, ['F5'])
        self.create_action('preferences', self.on_preferences_action, ['<primary>comma'])

    def do_activate(self):
        """Called when the application is activated"""
        if not self.window:
            if self.use_ide_mode:
                self.window = IDEWindow(application=self)
            else:
                self.window = MainWindow(application=self)
        self.window.present()

    def do_open(self, files, n_files, hint):
        """Called when files are opened with the application"""
        self.do_activate()
        if len(files) > 0:
            # Check if it's a project file
            filepath = files[0].get_path()
            if filepath.endswith('.nesproject'):
                if hasattr(self.window, 'project_manager'):
                    from pathlib import Path
                    self.window.project_manager.open_project(Path(filepath))
            else:
                # Open as regular file (CHR or source)
                if hasattr(self.window, 'open_file'):
                    self.window.open_file(filepath)

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
        if self.window and hasattr(self.window, 'show_open_dialog'):
            self.window.show_open_dialog()

    def on_save_action(self, action, param):
        """Save current file"""
        if self.window:
            if hasattr(self.window, 'save_file'):
                self.window.save_file()
            elif hasattr(self.window, 'editor_notebook'):
                try:
                    self.window.editor_notebook.save_current()
                except Exception as e:
                    print(f"Error saving: {e}")

    def on_save_as_action(self, action, param):
        """Save as dialog"""
        if self.window and hasattr(self.window, 'show_save_dialog'):
            self.window.show_save_dialog()

    def on_new_project_action(self, action, param):
        """Create new project"""
        if self.window and hasattr(self.window, 'project_manager'):
            self.window.project_manager.create_project(self.window)

    def on_open_project_action(self, action, param):
        """Open project"""
        if self.window and hasattr(self.window, '_show_open_project_dialog'):
            self.window._show_open_project_dialog()

    def on_close_project_action(self, action, param):
        """Close project"""
        if self.window and hasattr(self.window, 'project_manager'):
            self.window.project_manager.close_project()

    def on_build_action(self, action, param):
        """Build project"""
        if self.window and hasattr(self.window, '_on_build_clicked'):
            self.window._on_build_clicked()

    def on_run_action(self, action, param):
        """Run project"""
        if self.window and hasattr(self.window, '_on_run_clicked'):
            self.window._on_run_clicked()

    def on_preferences_action(self, action, param):
        """Show preferences"""
        # TODO: Implement preferences dialog
        dialog = Adw.MessageDialog(
            transient_for=self.window,
            heading='Preferences',
            body='Preferences dialog not yet implemented'
        )
        dialog.add_response('ok', 'OK')
        dialog.present()
