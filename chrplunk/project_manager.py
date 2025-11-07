"""Project Manager UI for NES IDE"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GObject, GLib
from pathlib import Path
from typing import Optional, Callable
import os

from chrplunk.project import NESProject, ProjectSettings, Assembler


class ProjectTreeRow(GObject.Object):
    """Data model for a file tree row"""

    def __init__(self, path: Path, is_directory: bool, display_name: str):
        super().__init__()
        self.path = path
        self.is_directory = is_directory
        self.display_name = display_name


class ProjectSidebar(Gtk.Box):
    """Sidebar showing project file tree"""

    __gsignals__ = {
        'file-activated': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.project: Optional[NESProject] = None

        # Create header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.set_margin_start(6)
        header.set_margin_end(6)
        header.set_margin_top(6)
        header.set_margin_bottom(6)

        label = Gtk.Label(label="Project")
        label.set_halign(Gtk.Align.START)
        label.add_css_class("heading")
        header.append(label)

        self.append(header)

        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        # Create tree view
        self.list_store = Gio.ListStore.new(ProjectTreeRow)
        self.tree_view = Gtk.ColumnView()
        self.tree_view.set_model(Gtk.NoSelection.new(self.list_store))
        self.tree_view.set_show_column_separators(False)
        self.tree_view.set_show_row_separators(False)

        # Create column for file names
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)

        column = Gtk.ColumnViewColumn(title="Files", factory=factory)
        column.set_expand(True)
        self.tree_view.append_column(column)

        # Handle activation
        gesture = Gtk.GestureClick()
        gesture.connect("pressed", self._on_item_clicked)
        self.tree_view.add_controller(gesture)

        scrolled.set_child(self.tree_view)
        self.append(scrolled)

        # Empty state
        self.empty_state = Adw.StatusPage(
            title="No Project Loaded",
            description="Create or open a project to get started",
            icon_name="folder-symbolic"
        )

        # Stack to switch between empty and tree
        self.stack = Gtk.Stack()
        self.stack.add_named(self.empty_state, "empty")
        self.stack.add_named(scrolled, "tree")
        self.stack.set_visible_child_name("empty")

        # Replace scrolled with stack
        self.remove(scrolled)
        self.append(self.stack)

    def _on_factory_setup(self, factory, list_item):
        """Setup list item widget"""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.set_margin_start(6)
        box.set_margin_end(6)
        box.set_margin_top(3)
        box.set_margin_bottom(3)

        icon = Gtk.Image()
        box.append(icon)

        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        box.append(label)

        list_item.set_child(box)

    def _on_factory_bind(self, factory, list_item):
        """Bind data to list item"""
        row: ProjectTreeRow = list_item.get_item()
        box = list_item.get_child()
        icon = box.get_first_child()
        label = box.get_last_child()

        # Set icon based on file type
        if row.is_directory:
            icon.set_from_icon_name("folder-symbolic")
        elif row.display_name.endswith(('.s', '.asm', '.inc')):
            icon.set_from_icon_name("text-x-generic-symbolic")
        elif row.display_name.endswith('.chr'):
            icon.set_from_icon_name("image-x-generic-symbolic")
        elif row.display_name.endswith('.nes'):
            icon.set_from_icon_name("application-x-executable-symbolic")
        else:
            icon.set_from_icon_name("text-x-generic-symbolic")

        label.set_text(row.display_name)

    def _on_item_clicked(self, gesture, n_press, x, y):
        """Handle item click"""
        if n_press == 2:  # Double click
            # Get the selected position
            widget = gesture.get_widget()

            # This is a simplified version - in a full implementation
            # we'd need to properly get the clicked item
            # For now, we'll need a different approach
            pass

    def set_project(self, project: NESProject):
        """Set the current project and populate tree"""
        self.project = project
        self._populate_tree()
        self.stack.set_visible_child_name("tree")

    def _populate_tree(self):
        """Populate the file tree from project"""
        self.list_store.remove_all()

        if not self.project:
            return

        # Add project directories and files
        self._add_directory_contents(self.project.root_path, "")

    def _add_directory_contents(self, dir_path: Path, prefix: str):
        """Recursively add directory contents"""
        try:
            items = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name))

            for item in items:
                # Skip hidden files and build directory
                if item.name.startswith('.') or item.name == 'build':
                    continue

                display_name = prefix + item.name
                row = ProjectTreeRow(item, item.is_dir(), display_name)
                self.list_store.append(row)

                # Recursively add subdirectories (up to 2 levels)
                if item.is_dir() and len(prefix) < 4:
                    self._add_directory_contents(item, prefix + "  ")

        except PermissionError:
            pass


class NewProjectDialog(Adw.Dialog):
    """Dialog for creating a new project"""

    __gsignals__ = {
        'project-created': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self, parent):
        super().__init__()
        self.set_title("New NES Project")

        # Create content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_start(24)
        content.set_margin_end(24)
        content.set_margin_top(24)
        content.set_margin_bottom(24)

        # Project name
        name_group = Adw.PreferencesGroup()
        name_group.set_title("Project Information")

        self.name_entry = Adw.EntryRow()
        self.name_entry.set_title("Project Name")
        self.name_entry.set_text("My NES Game")
        name_group.add(self.name_entry)

        self.author_entry = Adw.EntryRow()
        self.author_entry.set_title("Author")
        name_group.add(self.author_entry)

        content.append(name_group)

        # Location
        location_group = Adw.PreferencesGroup()
        location_group.set_title("Location")

        location_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.location_entry = Gtk.Entry()
        self.location_entry.set_hexpand(True)
        self.location_entry.set_text(os.path.expanduser("~/Projects"))
        location_box.append(self.location_entry)

        browse_button = Gtk.Button(label="Browse...")
        browse_button.connect("clicked", self._on_browse_clicked)
        location_box.append(browse_button)

        location_row = Adw.ActionRow()
        location_row.set_title("Project Location")
        location_row.add_suffix(location_box)
        location_group.add(location_row)

        content.append(location_group)

        # Template selection
        template_group = Adw.PreferencesGroup()
        template_group.set_title("Template")

        self.template_combo = Adw.ComboRow()
        self.template_combo.set_title("Project Template")

        templates = Gtk.StringList()
        templates.append("Empty Project")
        templates.append("Hello World")
        templates.append("Platformer")
        self.template_combo.set_model(templates)
        self.template_combo.set_selected(0)

        template_group.add(self.template_combo)
        content.append(template_group)

        # Assembler selection
        assembler_group = Adw.PreferencesGroup()
        assembler_group.set_title("Build System")

        self.assembler_combo = Adw.ComboRow()
        self.assembler_combo.set_title("Assembler")

        assemblers = Gtk.StringList()
        assemblers.append("ca65 (CC65 suite)")
        assemblers.append("asm6")
        assemblers.append("nesasm3")
        self.assembler_combo.set_model(assemblers)
        self.assembler_combo.set_selected(0)

        assembler_group.add(self.assembler_combo)
        content.append(assembler_group)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda b: self.close())
        button_box.append(cancel_button)

        create_button = Gtk.Button(label="Create Project")
        create_button.add_css_class("suggested-action")
        create_button.connect("clicked", self._on_create_clicked)
        button_box.append(create_button)

        content.append(button_box)

        # Set content
        self.set_child(content)

    def _on_browse_clicked(self, button):
        """Show directory chooser"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Choose Project Location")
        dialog.select_folder(None, None, self._on_folder_selected)

    def _on_folder_selected(self, dialog, result):
        """Handle folder selection"""
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                self.location_entry.set_text(folder.get_path())
        except GLib.Error:
            pass

    def _on_create_clicked(self, button):
        """Create the project"""
        name = self.name_entry.get_text()
        location = self.location_entry.get_text()
        author = self.author_entry.get_text()

        template_idx = self.template_combo.get_selected()
        template_names = ["empty", "hello", "platformer"]
        template = template_names[template_idx]

        assembler_idx = self.assembler_combo.get_selected()
        assembler_names = [Assembler.CA65.value, Assembler.ASM6.value, Assembler.NESASM3.value]
        assembler = assembler_names[assembler_idx]

        # Create project settings
        settings = ProjectSettings(
            name=name,
            author=author
        )

        # Update assembler in build configs
        for config in settings.build_configs.values():
            config['assembler'] = assembler

        # Create project directory
        project_dir = Path(location) / name.replace(" ", "_").lower()

        try:
            project = NESProject.create_new(project_dir, settings, template)
            self.emit('project-created', project)
            self.close()
        except Exception as e:
            dialog = Adw.MessageDialog(
                heading="Error Creating Project",
                body=str(e)
            )
            dialog.add_response("ok", "OK")
            dialog.present()


class ProjectManager(GObject.Object):
    """Manages the current project state"""

    __gsignals__ = {
        'project-opened': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'project-closed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__()
        self.current_project: Optional[NESProject] = None

    def create_project(self, parent_window) -> None:
        """Show new project dialog"""
        dialog = NewProjectDialog(parent_window)
        dialog.connect('project-created', self._on_project_created)
        dialog.present(parent_window)

    def _on_project_created(self, dialog, project: NESProject):
        """Handle project creation"""
        self.current_project = project
        self.emit('project-opened', project)

    def open_project(self, project_path: Path) -> None:
        """Open an existing project"""
        try:
            project = NESProject.load(project_path)
            self.current_project = project
            self.emit('project-opened', project)
        except Exception as e:
            raise

    def close_project(self) -> None:
        """Close the current project"""
        if self.current_project:
            self.current_project = None
            self.emit('project-closed')

    def get_current_project(self) -> Optional[NESProject]:
        """Get the currently open project"""
        return self.current_project
