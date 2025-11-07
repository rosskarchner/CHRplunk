"""Tile viewer and editor widget"""

import gi
gi.require_version('Gtk', '4.0')

from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, GObject
from chrplunk.chr_format import CHRFile, NES_PALETTE

class TileViewer(Gtk.DrawingArea):
    """Widget for viewing and editing CHR tiles"""

    __gsignals__ = {
        'tile-edited': (GObject.SignalFlags.RUN_FIRST, None, (int, object))
    }

    def __init__(self):
        super().__init__()

        self.chr_file = None
        self.scale = 3
        self.tiles_per_row = 16
        self.tile_size = 8 * self.scale
        self.selected_tile = None
        self.selected_color = 0
        self.editing_mode = False

        # Set up drawing
        self.set_draw_func(self.on_draw)

        # Set up gestures for interaction
        self.click_gesture = Gtk.GestureClick()
        self.click_gesture.connect('pressed', self.on_click)
        self.add_controller(self.click_gesture)

        self.drag_gesture = Gtk.GestureDrag()
        self.drag_gesture.connect('drag-update', self.on_drag)
        self.add_controller(self.drag_gesture)

        # Set content size
        self.set_content_width(self.tiles_per_row * self.tile_size)
        self.set_content_height(256)

    def set_chr_file(self, chr_file: CHRFile):
        """Set the CHR file to display"""
        self.chr_file = chr_file
        self.selected_tile = None

        # Update size
        if chr_file and chr_file.tile_count > 0:
            rows = (chr_file.tile_count + self.tiles_per_row - 1) // self.tiles_per_row
            height = rows * self.tile_size
            self.set_content_height(height)

        self.queue_draw()

    def on_draw(self, area, cr, width, height):
        """Draw the tiles"""
        if not self.chr_file or self.chr_file.tile_count == 0:
            return

        # Draw background
        cr.set_source_rgb(0.95, 0.95, 0.95)
        cr.paint()

        # Draw tiles
        for tile_idx in range(self.chr_file.tile_count):
            tile_row = tile_idx // self.tiles_per_row
            tile_col = tile_idx % self.tiles_per_row
            x = tile_col * self.tile_size
            y = tile_row * self.tile_size

            # Draw tile
            tile = self.chr_file.get_tile(tile_idx)
            self.draw_tile(cr, tile, x, y)

            # Draw selection border
            if tile_idx == self.selected_tile:
                cr.set_source_rgb(1.0, 0.5, 0.0)
                cr.set_line_width(2)
                cr.rectangle(x, y, self.tile_size, self.tile_size)
                cr.stroke()

            # Draw grid
            cr.set_source_rgba(0.7, 0.7, 0.7, 0.3)
            cr.set_line_width(1)
            cr.rectangle(x, y, self.tile_size, self.tile_size)
            cr.stroke()

    def draw_tile(self, cr, tile, x_offset, y_offset):
        """Draw a single tile"""
        for y in range(8):
            for x in range(8):
                color_idx = tile[y][x]
                color = NES_PALETTE[color_idx % len(NES_PALETTE)]
                cr.set_source_rgb(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)

                px = x_offset + x * self.scale
                py = y_offset + y * self.scale
                cr.rectangle(px, py, self.scale, self.scale)
                cr.fill()

    def on_click(self, gesture, n_press, x, y):
        """Handle click events"""
        if not self.chr_file:
            return

        tile_col = int(x // self.tile_size)
        tile_row = int(y // self.tile_size)
        tile_idx = tile_row * self.tiles_per_row + tile_col

        if tile_idx < self.chr_file.tile_count:
            if n_press == 1:
                # Single click - select tile
                self.selected_tile = tile_idx
                self.queue_draw()
            elif n_press == 2:
                # Double click - enter edit mode
                self.selected_tile = tile_idx
                self.editing_mode = True
                self.show_tile_editor(tile_idx)

        # If in editing mode, allow painting
        if self.editing_mode and self.selected_tile is not None:
            self.paint_pixel(x, y)

    def on_drag(self, gesture, x_offset, y_offset):
        """Handle drag events for painting"""
        if not self.editing_mode or not self.chr_file or self.selected_tile is None:
            return

        start_x, start_y = gesture.get_start_point()
        x = start_x + x_offset
        y = start_y + y_offset

        self.paint_pixel(x, y)

    def paint_pixel(self, x, y):
        """Paint a pixel when in editing mode"""
        if not self.editing_mode or self.selected_tile is None:
            return

        tile_col = int(x // self.tile_size)
        tile_row = int(y // self.tile_size)
        tile_idx = tile_row * self.tiles_per_row + tile_col

        if tile_idx != self.selected_tile:
            return

        # Calculate pixel within tile
        tile_x = int((x % self.tile_size) // self.scale)
        tile_y = int((y % self.tile_size) // self.scale)

        if 0 <= tile_x < 8 and 0 <= tile_y < 8:
            # Get current tile data
            tile = self.chr_file.get_tile(self.selected_tile)
            tile[tile_y][tile_x] = self.selected_color

            # Update CHR file
            self.chr_file.set_tile(self.selected_tile, tile)

            # Emit signal
            self.emit('tile-edited', self.selected_tile, tile)

            # Redraw
            self.queue_draw()

    def show_tile_editor(self, tile_idx):
        """Show tile editor dialog"""
        dialog = TileEditorDialog(self.get_root(), self.chr_file, tile_idx)
        dialog.connect('tile-changed', self.on_tile_changed)
        dialog.present()

    def on_tile_changed(self, dialog, tile_idx, tile_data):
        """Handle tile change from editor dialog"""
        self.chr_file.set_tile(tile_idx, tile_data)
        self.emit('tile-edited', tile_idx, tile_data)
        self.queue_draw()


class TileEditorDialog(Gtk.Window):
    """Dialog for editing a single tile with a larger view"""

    __gsignals__ = {
        'tile-changed': (GObject.SignalFlags.RUN_FIRST, None, (int, object))
    }

    def __init__(self, parent, chr_file, tile_idx):
        super().__init__()

        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title(f'Edit Tile {tile_idx}')
        self.set_default_size(500, 550)

        self.chr_file = chr_file
        self.tile_idx = tile_idx
        self.tile_data = [row[:] for row in chr_file.get_tile(tile_idx)]  # Deep copy
        self.scale = 20
        self.selected_color = 0

        # Create layout
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)

        # Create drawing area for tile
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_content_width(8 * self.scale)
        self.drawing_area.set_content_height(8 * self.scale)
        self.drawing_area.set_draw_func(self.on_draw)

        # Add click handling
        click = Gtk.GestureClick()
        click.connect('pressed', self.on_click)
        self.drawing_area.add_controller(click)

        # Add drag handling
        drag = Gtk.GestureDrag()
        drag.connect('drag-update', self.on_drag)
        self.drawing_area.add_controller(drag)

        # Center the drawing area
        drawing_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        drawing_box.set_halign(Gtk.Align.CENTER)
        drawing_box.append(self.drawing_area)

        box.append(drawing_box)

        # Color palette selector
        palette_label = Gtk.Label(label='Select Color:')
        palette_label.set_halign(Gtk.Align.START)
        box.append(palette_label)

        palette_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        palette_box.set_halign(Gtk.Align.CENTER)

        for i in range(4):
            btn = Gtk.ToggleButton()
            btn.set_size_request(40, 40)

            # Create colored square
            drawing = Gtk.DrawingArea()
            drawing.set_content_width(40)
            drawing.set_content_height(40)
            color = NES_PALETTE[i]
            drawing.set_draw_func(lambda area, cr, w, h, col=color:
                                  (cr.set_source_rgb(col[0]/255, col[1]/255, col[2]/255),
                                   cr.rectangle(0, 0, w, h),
                                   cr.fill()))
            btn.set_child(drawing)

            if i == 0:
                btn.set_active(True)

            btn.connect('toggled', self.on_color_selected, i)
            palette_box.append(btn)

            # Store button for later
            if not hasattr(self, 'color_buttons'):
                self.color_buttons = []
            self.color_buttons.append(btn)

        box.append(palette_box)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(10)

        cancel_btn = Gtk.Button(label='Cancel')
        cancel_btn.connect('clicked', lambda x: self.close())
        button_box.append(cancel_btn)

        save_btn = Gtk.Button(label='Save')
        save_btn.add_css_class('suggested-action')
        save_btn.connect('clicked', self.on_save)
        button_box.append(save_btn)

        box.append(button_box)

        self.set_child(box)

    def on_draw(self, area, cr, width, height):
        """Draw the tile"""
        # Draw grid background
        cr.set_source_rgb(0.9, 0.9, 0.9)
        cr.paint()

        # Draw pixels
        for y in range(8):
            for x in range(8):
                color_idx = self.tile_data[y][x]
                color = NES_PALETTE[color_idx % len(NES_PALETTE)]
                cr.set_source_rgb(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)

                px = x * self.scale
                py = y * self.scale
                cr.rectangle(px, py, self.scale, self.scale)
                cr.fill()

        # Draw grid
        cr.set_source_rgb(0.6, 0.6, 0.6)
        cr.set_line_width(1)
        for i in range(9):
            cr.move_to(i * self.scale, 0)
            cr.line_to(i * self.scale, 8 * self.scale)
            cr.move_to(0, i * self.scale)
            cr.line_to(8 * self.scale, i * self.scale)
        cr.stroke()

    def on_click(self, gesture, n_press, x, y):
        """Handle click to paint pixel"""
        self.paint_pixel(x, y)

    def on_drag(self, gesture, x_offset, y_offset):
        """Handle drag to paint"""
        start_x, start_y = gesture.get_start_point()
        x = start_x + x_offset
        y = start_y + y_offset
        self.paint_pixel(x, y)

    def paint_pixel(self, x, y):
        """Paint a pixel"""
        px = int(x // self.scale)
        py = int(y // self.scale)

        if 0 <= px < 8 and 0 <= py < 8:
            self.tile_data[py][px] = self.selected_color
            self.drawing_area.queue_draw()

    def on_color_selected(self, button, color_idx):
        """Handle color selection"""
        if button.get_active():
            self.selected_color = color_idx
            # Deactivate other buttons
            for i, btn in enumerate(self.color_buttons):
                if i != color_idx:
                    btn.set_active(False)

    def on_save(self, button):
        """Save the tile"""
        self.emit('tile-changed', self.tile_idx, self.tile_data)
        self.close()
