"""Build system integration for NES projects"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GObject, GLib, Pango
from pathlib import Path
from typing import Optional, List, Dict
import subprocess
import threading
import re
import os


class BuildError:
    """Represents a build error or warning"""

    def __init__(self, filepath: str, line: int, column: int, message: str,
                 error_type: str = "error"):
        self.filepath = filepath
        self.line = line
        self.column = column
        self.message = message
        self.error_type = error_type  # "error" or "warning"


class BuildOutput(Gtk.Box):
    """Widget for displaying build output"""

    __gsignals__ = {
        'error-clicked': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Create text view for output
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_monospace(True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.NONE)

        # Set font
        font_desc = Pango.FontDescription.from_string("Monospace 10")
        self.text_view.override_font(font_desc)

        self.buffer = self.text_view.get_buffer()

        # Create tags for formatting
        self.buffer.create_tag("error", foreground="red", weight=Pango.Weight.BOLD)
        self.buffer.create_tag("warning", foreground="orange", weight=Pango.Weight.BOLD)
        self.buffer.create_tag("success", foreground="green", weight=Pango.Weight.BOLD)
        self.buffer.create_tag("info", foreground="blue")

        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.text_view)
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        self.append(scrolled)

        self.errors: List[BuildError] = []

    def clear(self):
        """Clear the output"""
        self.buffer.set_text("")
        self.errors.clear()

    def append_text(self, text: str, tag: Optional[str] = None):
        """Append text to the output"""
        end_iter = self.buffer.get_end_iter()
        if tag:
            self.buffer.insert_with_tags_by_name(end_iter, text, tag)
        else:
            self.buffer.insert(end_iter, text)

        # Auto-scroll to bottom
        mark = self.buffer.get_insert()
        self.text_view.scroll_mark_onscreen(mark)

    def append_line(self, text: str, tag: Optional[str] = None):
        """Append a line of text"""
        self.append_text(text + "\n", tag)

    def add_error(self, error: BuildError):
        """Add a build error"""
        self.errors.append(error)


class BuildPanel(Gtk.Box):
    """Panel with tabs for build output, console, etc."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Create notebook
        self.notebook = Gtk.Notebook()
        self.notebook.set_show_border(False)

        # Build output tab
        self.build_output = BuildOutput()
        self.notebook.append_page(self.build_output, Gtk.Label(label="Build Output"))

        # Console tab (future)
        console_label = Gtk.Label(label="Console output will go here")
        self.notebook.append_page(console_label, Gtk.Label(label="Console"))

        # Problems tab (future)
        problems_label = Gtk.Label(label="Problems will be listed here")
        self.notebook.append_page(problems_label, Gtk.Label(label="Problems"))

        self.append(self.notebook)

    def get_build_output(self) -> BuildOutput:
        """Get the build output widget"""
        return self.build_output

    def show_build_output(self):
        """Switch to build output tab"""
        self.notebook.set_current_page(0)


class BuildSystem(GObject.Object):
    """Build system manager"""

    __gsignals__ = {
        'build-started': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'build-finished': (GObject.SignalFlags.RUN_FIRST, None, (bool, str)),
        'build-output': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__()
        self.current_process: Optional[subprocess.Popen] = None
        self.is_building = False

    def build_project(self, project, build_panel: BuildPanel):
        """Build a project"""
        if self.is_building:
            return

        from chrplunk.project import NESProject, Assembler

        if not isinstance(project, NESProject):
            return

        self.is_building = True
        self.emit('build-started')

        # Get build configuration
        config = project.get_active_build_config()

        # Clear output
        output = build_panel.get_build_output()
        output.clear()

        # Show build panel
        build_panel.show_build_output()

        # Run build in thread
        thread = threading.Thread(
            target=self._build_thread,
            args=(project, config, output)
        )
        thread.daemon = True
        thread.start()

    def _build_thread(self, project, config, output: BuildOutput):
        """Build thread (runs in background)"""
        try:
            # Determine build command based on assembler
            assembler = config.get('assembler', 'ca65')

            if assembler == 'ca65':
                success = self._build_ca65(project, config, output)
            elif assembler == 'asm6':
                success = self._build_asm6(project, config, output)
            else:
                GLib.idle_add(output.append_line, f"Unsupported assembler: {assembler}", "error")
                success = False

            # Emit build finished signal
            result_msg = "Build succeeded" if success else "Build failed"
            GLib.idle_add(self._on_build_finished, success, result_msg)

        except Exception as e:
            GLib.idle_add(output.append_line, f"Build error: {str(e)}", "error")
            GLib.idle_add(self._on_build_finished, False, str(e))

    def _build_ca65(self, project, config, output: BuildOutput) -> bool:
        """Build using ca65 assembler"""
        GLib.idle_add(output.append_line, "Building with ca65...", "info")

        # Get paths
        source_dir = project.root_path / project.settings.source_dir
        build_dir = project.root_path / project.settings.build_dir
        build_dir.mkdir(exist_ok=True)

        main_source = project.root_path / project.settings.main_source

        if not main_source.exists():
            GLib.idle_add(output.append_line, f"Main source file not found: {main_source}", "error")
            return False

        # Get assembler and linker paths
        assembler_path = config.get('assembler_path', 'ca65')
        linker_path = config.get('linker_path', 'ld65')

        # Assemble
        obj_file = build_dir / 'main.o'
        asm_flags = config.get('assembler_flags', [])

        asm_cmd = [assembler_path] + asm_flags + ['-o', str(obj_file), str(main_source)]

        GLib.idle_add(output.append_line, f"$ {' '.join(asm_cmd)}")

        try:
            result = subprocess.run(
                asm_cmd,
                cwd=str(project.root_path),
                capture_output=True,
                text=True
            )

            if result.stdout:
                GLib.idle_add(output.append_text, result.stdout)
            if result.stderr:
                GLib.idle_add(output.append_text, result.stderr)

            if result.returncode != 0:
                GLib.idle_add(output.append_line, "Assembly failed", "error")
                self._parse_ca65_errors(result.stderr, output)
                return False

        except FileNotFoundError:
            GLib.idle_add(output.append_line, f"Assembler not found: {assembler_path}", "error")
            GLib.idle_add(output.append_line, "Please install cc65 or update the assembler path", "info")
            return False

        # Link
        output_file = build_dir / config.get('output_filename', 'game.nes')
        linker_flags = config.get('linker_flags', [])

        # Check for linker config
        linker_config = source_dir / 'nes.cfg'
        if linker_config.exists():
            link_cmd = [linker_path, '-C', str(linker_config)] + linker_flags + ['-o', str(output_file), str(obj_file)]
        else:
            link_cmd = [linker_path, '-t', 'nes'] + linker_flags + ['-o', str(output_file), str(obj_file)]

        GLib.idle_add(output.append_line, f"$ {' '.join(link_cmd)}")

        try:
            result = subprocess.run(
                link_cmd,
                cwd=str(project.root_path),
                capture_output=True,
                text=True
            )

            if result.stdout:
                GLib.idle_add(output.append_text, result.stdout)
            if result.stderr:
                GLib.idle_add(output.append_text, result.stderr)

            if result.returncode != 0:
                GLib.idle_add(output.append_line, "Linking failed", "error")
                return False

        except FileNotFoundError:
            GLib.idle_add(output.append_line, f"Linker not found: {linker_path}", "error")
            return False

        GLib.idle_add(output.append_line, f"Build succeeded: {output_file}", "success")
        return True

    def _build_asm6(self, project, config, output: BuildOutput) -> bool:
        """Build using asm6 assembler"""
        GLib.idle_add(output.append_line, "Building with asm6...", "info")

        # Get paths
        build_dir = project.root_path / project.settings.build_dir
        build_dir.mkdir(exist_ok=True)

        main_source = project.root_path / project.settings.main_source

        if not main_source.exists():
            GLib.idle_add(output.append_line, f"Main source file not found: {main_source}", "error")
            return False

        # Get assembler path
        assembler_path = config.get('assembler_path', 'asm6')

        # Assemble
        output_file = build_dir / config.get('output_filename', 'game.nes')
        asm_flags = config.get('assembler_flags', [])

        asm_cmd = [assembler_path] + asm_flags + [str(main_source), str(output_file)]

        GLib.idle_add(output.append_line, f"$ {' '.join(asm_cmd)}")

        try:
            result = subprocess.run(
                asm_cmd,
                cwd=str(project.root_path),
                capture_output=True,
                text=True
            )

            if result.stdout:
                GLib.idle_add(output.append_text, result.stdout)
            if result.stderr:
                GLib.idle_add(output.append_text, result.stderr)

            if result.returncode != 0:
                GLib.idle_add(output.append_line, "Assembly failed", "error")
                return False

            GLib.idle_add(output.append_line, f"Build succeeded: {output_file}", "success")
            return True

        except FileNotFoundError:
            GLib.idle_add(output.append_line, f"Assembler not found: {assembler_path}", "error")
            return False

    def _parse_ca65_errors(self, stderr: str, output: BuildOutput):
        """Parse ca65 error output"""
        # ca65 error format: filename(line): Error: message
        error_pattern = re.compile(r'(.+?)\((\d+)\):\s+(Error|Warning):\s+(.+)')

        for line in stderr.split('\n'):
            match = error_pattern.match(line)
            if match:
                filepath = match.group(1)
                line_num = int(match.group(2))
                error_type = match.group(3).lower()
                message = match.group(4)

                error = BuildError(filepath, line_num, 0, message, error_type)
                output.add_error(error)

    def _on_build_finished(self, success: bool, message: str):
        """Called when build finishes"""
        self.is_building = False
        self.emit('build-finished', success, message)

    def cancel_build(self):
        """Cancel the current build"""
        if self.current_process and self.current_process.poll() is None:
            self.current_process.terminate()
            self.is_building = False
