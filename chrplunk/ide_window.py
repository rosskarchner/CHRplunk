"""Main IDE window with multi-panel architecture"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('GtkSource', '5')

from gi.repository import Gtk, Adw, Gio, GLib, GtkSource
from pathlib import Path
from typing import Optional
import os
import subprocess

from chrplunk.project import NESProject
from chrplunk.project_manager import ProjectManager, ProjectSidebar
from chrplunk.code_editor import EditorNotebook
from chrplunk.build_system import BuildSystem, BuildPanel
from chrplunk.tile_viewer import TileViewer
from chrplunk.palette_editor import PaletteEditor
from chrplunk.chr_format import CHRFile, NES_PALETTE


class IDEWindow(Adw.ApplicationWindow):
    """Main IDE window with multi-panel architecture"""

    def __init__(self, application):
        super().__init__(application=application)

        self.set_title('CHRplunk NES IDE')
        self.set_default_size(1200, 800)

        # Initialize managers
        self.project_manager = ProjectManager()
        self.project_manager.connect('project-opened', self._on_project_opened)
        self.project_manager.connect('project-closed', self._on_project_closed)

        self.build_system = BuildSystem()
        self.build_system.connect('build-finished', self._on_build_finished)

        # Current state
        self.current_project: Optional[NESProject] = None
        self.chr_file = None
        self.current_palette = list(NES_PALETTE)

        # Setup language manager for code editor
        self._setup_language_manager()

        # Create UI
        self._create_ui()

    def _setup_language_manager(self):
        """Setup GtkSourceView language manager with custom language specs"""
        lang_manager = GtkSource.LanguageManager.get_default()

        # Add our custom language specs directory
        data_dir = Path(__file__).parent.parent / 'data' / 'language-specs'
        if data_dir.exists():
            search_paths = list(lang_manager.get_search_path())
            search_paths.insert(0, str(data_dir))
            lang_manager.set_search_path(search_paths)

    def _create_ui(self):
        """Create the main UI layout"""
        # Create header bar
        self._create_header_bar()

        # Create main content area
        self.toolbox = Adw.ToolbarView()
        self.toolbox.add_top_bar(self.header_bar)

        # Create horizontal paned for sidebar and main area
        self.main_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_paned.set_shrink_start_child(False)
        self.main_paned.set_shrink_end_child(False)
        self.main_paned.set_resize_start_child(False)
        self.main_paned.set_resize_end_child(True)

        # Create sidebar
        self.sidebar = ProjectSidebar()
        self.sidebar.set_size_request(200, -1)
        self.main_paned.set_start_child(self.sidebar)

        # Create vertical paned for editor and build panel
        self.vertical_paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.vertical_paned.set_shrink_start_child(False)
        self.vertical_paned.set_shrink_end_child(False)
        self.vertical_paned.set_resize_start_child(True)
        self.vertical_paned.set_resize_end_child(False)

        # Create main editor area (notebook with tabs)
        self.editor_notebook = EditorNotebook()
        self.editor_notebook.connect('file-opened', self._on_file_opened)
        self.vertical_paned.set_start_child(self.editor_notebook)

        # Create build panel
        self.build_panel = BuildPanel()
        self.build_panel.set_size_request(-1, 200)
        self.vertical_paned.set_end_child(self.build_panel)

        # Set vertical paned position (start with build panel collapsed)
        self.vertical_paned.set_position(600)

        self.main_paned.set_end_child(self.vertical_paned)

        # Set horizontal paned position
        self.main_paned.set_position(250)

        # Create welcome page
        self.welcome_page = self._create_welcome_page()

        # Create stack to switch between welcome and IDE
        self.stack = Gtk.Stack()
        self.stack.add_named(self.welcome_page, 'welcome')
        self.stack.add_named(self.main_paned, 'ide')
        self.stack.set_visible_child_name('welcome')

        self.toolbox.set_content(self.stack)
        self.set_content(self.toolbox)

    def _create_header_bar(self):
        """Create the header bar with menus and actions"""
        self.header_bar = Adw.HeaderBar()

        # Left section - Project and File operations
        left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Project menu
        project_menu_button = Gtk.MenuButton()
        project_menu_button.set_icon_name('document-open-symbolic')
        project_menu_button.set_tooltip_text('Project')

        project_menu = Gio.Menu()
        project_menu.append('New Project...', 'app.new-project')
        project_menu.append('Open Project...', 'app.open-project')
        project_menu.append('Close Project', 'app.close-project')
        project_menu_button.set_menu_model(project_menu)

        left_box.append(project_menu_button)

        # Save button
        self.save_button = Gtk.Button(icon_name='document-save-symbolic')
        self.save_button.set_tooltip_text('Save (Ctrl+S)')
        self.save_button.connect('clicked', lambda b: self._on_save_clicked())
        self.save_button.set_sensitive(False)
        left_box.append(self.save_button)

        self.header_bar.pack_start(left_box)

        # Center section - Build and Run controls
        center_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        center_box.add_css_class('linked')

        # Build button
        self.build_button = Gtk.Button(label='Build')
        self.build_button.set_icon_name('system-run-symbolic')
        self.build_button.set_tooltip_text('Build Project (F7)')
        self.build_button.connect('clicked', lambda b: self._on_build_clicked())
        self.build_button.set_sensitive(False)
        center_box.append(self.build_button)

        # Run button
        self.run_button = Gtk.Button(label='Run')
        self.run_button.set_icon_name('media-playback-start-symbolic')
        self.run_button.set_tooltip_text('Build & Run (F5)')
        self.run_button.connect('clicked', lambda b: self._on_run_clicked())
        self.run_button.set_sensitive(False)
        center_box.append(self.run_button)

        self.header_bar.set_title_widget(center_box)

        # Right section - App menu
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name('open-menu-symbolic')

        app_menu = Gio.Menu()
        app_menu.append('Preferences', 'app.preferences')
        app_menu.append('About CHRplunk', 'app.about')
        app_menu.append('Quit', 'app.quit')
        menu_button.set_menu_model(app_menu)

        self.header_bar.pack_end(menu_button)

    def _create_welcome_page(self) -> Gtk.Widget:
        """Create welcome page shown when no project is open"""
        welcome = Adw.StatusPage(
            title='Welcome to CHRplunk NES IDE',
            description='Create or open a project to start developing NES games',
            icon_name='applications-games-symbolic'
        )

        # Add action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(24)

        new_project_button = Gtk.Button(label='New Project')
        new_project_button.add_css_class('pill')
        new_project_button.add_css_class('suggested-action')
        new_project_button.connect('clicked', lambda b: self.project_manager.create_project(self))
        button_box.append(new_project_button)

        open_project_button = Gtk.Button(label='Open Project')
        open_project_button.add_css_class('pill')
        open_project_button.connect('clicked', lambda b: self._show_open_project_dialog())
        button_box.append(open_project_button)

        # Create container
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.append(welcome)
        container.append(button_box)

        return container

    def _show_open_project_dialog(self):
        """Show dialog to open a project"""
        dialog = Gtk.FileDialog()
        dialog.set_title('Open NES Project')

        # Create file filter
        filter_project = Gtk.FileFilter()
        filter_project.set_name('NES Project')
        filter_project.add_pattern('.nesproject')

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_project)
        dialog.set_filters(filters)

        dialog.open(self, None, self._on_open_project_response)

    def _on_open_project_response(self, dialog, result):
        """Handle open project dialog response"""
        try:
            file = dialog.open_finish(result)
            if file:
                project_path = Path(file.get_path())
                self.project_manager.open_project(project_path)
        except GLib.Error as e:
            if e.code != 2:  # Not a dismiss error
                self._show_error_dialog('Error Opening Project', str(e))

    def _on_project_opened(self, manager, project: NESProject):
        """Handle project opened event"""
        self.current_project = project

        # Update UI
        self.sidebar.set_project(project)
        self.stack.set_visible_child_name('ide')

        # Enable build buttons
        self.build_button.set_sensitive(True)
        self.run_button.set_sensitive(True)

        # Update title
        self.set_title(f'{project.settings.name} - CHRplunk NES IDE')

        # Open main source file if it exists
        main_source = project.root_path / project.settings.main_source
        if main_source.exists():
            self.editor_notebook.open_file(main_source)

    def _on_project_closed(self, manager):
        """Handle project closed event"""
        self.current_project = None

        # Update UI
        self.stack.set_visible_child_name('welcome')

        # Disable build buttons
        self.build_button.set_sensitive(False)
        self.run_button.set_sensitive(False)

        # Reset title
        self.set_title('CHRplunk NES IDE')

    def _on_file_opened(self, notebook, filepath: str):
        """Handle file opened in editor"""
        # Enable save button
        self.save_button.set_sensitive(True)

    def _on_save_clicked(self):
        """Handle save button clicked"""
        try:
            self.editor_notebook.save_current()
        except Exception as e:
            self._show_error_dialog('Error Saving File', str(e))

    def _on_build_clicked(self):
        """Handle build button clicked"""
        if self.current_project:
            # Save all open files
            self.editor_notebook.save_all()

            # Run build
            self.build_system.build_project(self.current_project, self.build_panel)

    def _on_run_clicked(self):
        """Handle run button clicked"""
        if not self.current_project:
            return

        # Build first
        self._on_build_clicked()

        # The actual run will happen in build_finished handler

    def _on_build_finished(self, build_system, success: bool, message: str):
        """Handle build finished event"""
        if success:
            # Show success message
            self._show_toast('Build succeeded')

            # If run was requested, launch emulator
            # (We'll detect this by checking if run button was the trigger)
            # For now, just show the message
        else:
            self._show_toast('Build failed')

    def _run_in_emulator(self):
        """Run the built ROM in an emulator"""
        if not self.current_project:
            return

        # Get ROM path
        build_dir = self.current_project.root_path / self.current_project.settings.build_dir
        config = self.current_project.get_active_build_config()
        rom_file = build_dir / config.get('output_filename', 'game.nes')

        if not rom_file.exists():
            self._show_error_dialog('ROM Not Found', f'Built ROM not found: {rom_file}')
            return

        # Get emulator path
        emulator_path = self.current_project.settings.emulator_path

        if not emulator_path:
            self._show_error_dialog('Emulator Not Configured',
                                    'Please set an emulator path in project settings')
            return

        # Launch emulator
        try:
            subprocess.Popen([emulator_path, str(rom_file)])
        except Exception as e:
            self._show_error_dialog('Error Launching Emulator', str(e))

    def _show_error_dialog(self, heading: str, body: str):
        """Show an error dialog"""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=heading,
            body=body
        )
        dialog.add_response('ok', 'OK')
        dialog.present()

    def _show_toast(self, message: str):
        """Show a toast notification"""
        toast = Adw.Toast(title=message)
        toast.set_timeout(2)

        # Get or create toast overlay
        if not hasattr(self, 'toast_overlay'):
            self.toast_overlay = Adw.ToastOverlay()
            self.toast_overlay.set_child(self.stack)
            self.toolbox.set_content(self.toast_overlay)

        self.toast_overlay.add_toast(toast)
