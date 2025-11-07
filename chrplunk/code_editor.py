"""Code editor for assembly files"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GtkSource', '5')

from gi.repository import Gtk, GtkSource, Gio, GObject, Pango
from pathlib import Path
from typing import Optional


class CodeEditorView(GtkSource.View):
    """Enhanced source code editor view"""

    def __init__(self):
        super().__init__()

        # Configure view
        self.set_show_line_numbers(True)
        self.set_highlight_current_line(True)
        self.set_auto_indent(True)
        self.set_indent_on_tab(True)
        self.set_tab_width(4)
        self.set_insert_spaces_instead_of_tabs(True)
        self.set_show_right_margin(False)
        self.set_monospace(True)

        # Set font
        font_desc = Pango.FontDescription.from_string("Monospace 11")
        self.set_font_desc(font_desc)

        # Enable bracket matching
        buffer = self.get_buffer()
        if isinstance(buffer, GtkSource.Buffer):
            buffer.set_highlight_matching_brackets(True)

    def set_font_desc(self, font_desc: Pango.FontDescription):
        """Set the font description"""
        self.modify_font(font_desc)


class CodeEditor(Gtk.Box):
    """Code editor widget with source view and extras"""

    __gsignals__ = {
        'file-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'file-saved': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.current_file: Optional[Path] = None
        self.is_modified = False

        # Create language manager
        self.language_manager = GtkSource.LanguageManager.get_default()

        # Create style scheme manager
        self.style_manager = GtkSource.StyleSchemeManager.get_default()

        # Create source buffer
        self.buffer = GtkSource.Buffer()
        self.buffer.connect('changed', self._on_buffer_changed)

        # Try to set 6502 language (will create this next)
        language = self.language_manager.get_language('6502asm')
        if language:
            self.buffer.set_language(language)

        # Set style scheme
        scheme = self.style_manager.get_scheme('Adwaita')
        if scheme:
            self.buffer.set_style_scheme(scheme)

        # Create source view
        self.source_view = CodeEditorView()
        self.source_view.set_buffer(self.buffer)

        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.source_view)
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        self.append(scrolled)

    def load_file(self, filepath: Path):
        """Load a file into the editor"""
        try:
            with open(filepath, 'r') as f:
                content = f.read()

            self.buffer.begin_not_undoable_action()
            self.buffer.set_text(content)
            self.buffer.end_not_undoable_action()

            self.current_file = filepath
            self.is_modified = False

            # Set language based on file extension
            self._detect_language(filepath)

            # Place cursor at beginning
            self.buffer.place_cursor(self.buffer.get_start_iter())

        except Exception as e:
            print(f"Error loading file: {e}")
            raise

    def save_file(self, filepath: Optional[Path] = None):
        """Save the current content to file"""
        if filepath is None:
            filepath = self.current_file

        if filepath is None:
            raise ValueError("No file path specified")

        try:
            start = self.buffer.get_start_iter()
            end = self.buffer.get_end_iter()
            content = self.buffer.get_text(start, end, False)

            with open(filepath, 'w') as f:
                f.write(content)

            self.current_file = filepath
            self.is_modified = False
            self.emit('file-saved', str(filepath))

        except Exception as e:
            print(f"Error saving file: {e}")
            raise

    def get_text(self) -> str:
        """Get the current text content"""
        start = self.buffer.get_start_iter()
        end = self.buffer.get_end_iter()
        return self.buffer.get_text(start, end, False)

    def set_text(self, text: str):
        """Set the text content"""
        self.buffer.set_text(text)

    def _on_buffer_changed(self, buffer):
        """Handle buffer changes"""
        if not self.is_modified:
            self.is_modified = True
            self.emit('file-changed')

    def _detect_language(self, filepath: Path):
        """Detect and set language based on file extension"""
        ext = filepath.suffix.lower()

        # Map extensions to language IDs
        lang_map = {
            '.s': '6502asm',
            '.asm': '6502asm',
            '.inc': '6502asm',
            '.c': 'c',
            '.h': 'c',
            '.py': 'python',
            '.json': 'json',
            '.xml': 'xml',
            '.cfg': 'ini',
        }

        lang_id = lang_map.get(ext)
        if lang_id:
            language = self.language_manager.get_language(lang_id)
            if language:
                self.buffer.set_language(language)

    def get_current_file(self) -> Optional[Path]:
        """Get the current file path"""
        return self.current_file

    def is_file_modified(self) -> bool:
        """Check if the file has been modified"""
        return self.is_modified


class EditorNotebook(Gtk.Notebook):
    """Notebook widget for managing multiple editor tabs"""

    __gsignals__ = {
        'file-opened': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'file-closed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__()

        self.set_scrollable(True)
        self.set_show_border(False)

        # Map of file paths to editor widgets
        self.editors = {}

    def open_file(self, filepath: Path) -> CodeEditor:
        """Open a file in a new tab or switch to existing tab"""
        filepath = Path(filepath)
        filepath_str = str(filepath)

        # Check if file is already open
        if filepath_str in self.editors:
            editor, page_num = self.editors[filepath_str]
            self.set_current_page(page_num)
            return editor

        # Create new editor
        editor = CodeEditor()

        try:
            editor.load_file(filepath)
        except Exception as e:
            raise

        # Create tab label with close button
        tab_label = self._create_tab_label(filepath.name, filepath_str)

        # Add to notebook
        page_num = self.append_page(editor, tab_label)
        self.set_tab_reorderable(editor, True)

        # Store in map
        self.editors[filepath_str] = (editor, page_num)

        # Switch to new tab
        self.set_current_page(page_num)

        # Emit signal
        self.emit('file-opened', filepath_str)

        return editor

    def close_file(self, filepath: str):
        """Close a file tab"""
        if filepath in self.editors:
            editor, page_num = self.editors[filepath]

            # Check if modified
            if editor.is_file_modified():
                # TODO: Show save dialog
                pass

            # Remove from notebook
            self.remove_page(page_num)

            # Remove from map
            del self.editors[filepath]

            # Update page numbers for remaining editors
            self._update_page_numbers()

            # Emit signal
            self.emit('file-closed', filepath)

    def close_current(self):
        """Close the current tab"""
        current_page = self.get_current_page()
        if current_page >= 0:
            widget = self.get_nth_page(current_page)
            if widget:
                # Find the filepath for this widget
                for filepath, (editor, page_num) in self.editors.items():
                    if editor == widget:
                        self.close_file(filepath)
                        break

    def get_current_editor(self) -> Optional[CodeEditor]:
        """Get the currently active editor"""
        current_page = self.get_current_page()
        if current_page >= 0:
            widget = self.get_nth_page(current_page)
            if isinstance(widget, CodeEditor):
                return widget
        return None

    def save_current(self):
        """Save the current editor"""
        editor = self.get_current_editor()
        if editor:
            try:
                editor.save_file()
            except Exception as e:
                raise

    def save_all(self):
        """Save all modified editors"""
        for filepath, (editor, _) in self.editors.items():
            if editor.is_file_modified():
                try:
                    editor.save_file()
                except Exception as e:
                    print(f"Error saving {filepath}: {e}")

    def _create_tab_label(self, filename: str, filepath: str) -> Gtk.Box:
        """Create a tab label with close button"""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        label = Gtk.Label(label=filename)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_max_width_chars(20)
        box.append(label)

        close_button = Gtk.Button()
        close_button.set_icon_name('window-close-symbolic')
        close_button.add_css_class('flat')
        close_button.set_tooltip_text('Close')
        close_button.connect('clicked', lambda b: self.close_file(filepath))
        box.append(close_button)

        return box

    def _update_page_numbers(self):
        """Update stored page numbers after a tab is closed"""
        new_editors = {}
        for i in range(self.get_n_pages()):
            widget = self.get_nth_page(i)
            # Find this widget in the map
            for filepath, (editor, old_page_num) in self.editors.items():
                if editor == widget:
                    new_editors[filepath] = (editor, i)
                    break
        self.editors = new_editors
