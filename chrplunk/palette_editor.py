"""Palette editor widget"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')

from gi.repository import Gtk, Gdk, GObject

class PaletteEditor(Gtk.Box):
    """Widget for editing the color palette"""

    __gsignals__ = {
        'palette-changed': (GObject.SignalFlags.RUN_FIRST, None, (object,))
    }

    def __init__(self, palette):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        self.palette = [tuple(c) for c in palette]  # Store as tuples
        self.color_buttons = []

        # Set fixed width
        self.set_size_request(250, -1)

        # Add margins
        self.set_margin_start(10)
        self.set_margin_end(10)
        self.set_margin_top(10)
        self.set_margin_bottom(10)

        # Title
        title = Gtk.Label()
        title.set_markup('<b>Color Palette</b>')
        title.set_halign(Gtk.Align.START)
        self.append(title)

        # Description
        desc = Gtk.Label(label='Click a color to edit it')
        desc.set_halign(Gtk.Align.START)
        desc.add_css_class('dim-label')
        self.append(desc)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.append(sep)

        # Color swatches
        for i in range(4):
            color_row = self.create_color_row(i)
            self.append(color_row)

        # Reset button
        reset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        reset_box.set_halign(Gtk.Align.CENTER)
        reset_box.set_margin_top(20)

        reset_btn = Gtk.Button(label='Reset to Default')
        reset_btn.connect('clicked', self.on_reset_clicked)
        reset_box.append(reset_btn)

        self.append(reset_box)

    def create_color_row(self, index):
        """Create a row for a single color"""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row.set_margin_top(5)
        row.set_margin_bottom(5)

        # Color label
        label = Gtk.Label(label=f'Color {index}:')
        label.set_width_chars(8)
        label.set_xalign(0)
        row.append(label)

        # Color button
        color_btn = Gtk.Button()
        color_btn.set_size_request(100, 40)

        # Create drawing area for color swatch
        drawing = Gtk.DrawingArea()
        drawing.set_content_width(100)
        drawing.set_content_height(40)
        color = self.palette[index]
        drawing.set_draw_func(lambda area, cr, w, h, col=color:
                              (cr.set_source_rgb(col[0]/255, col[1]/255, col[2]/255),
                               cr.rectangle(0, 0, w, h),
                               cr.fill()))
        color_btn.set_child(drawing)
        color_btn.connect('clicked', self.on_color_clicked, index)

        row.append(color_btn)

        # Store button reference
        self.color_buttons.append((color_btn, drawing))

        # RGB label
        rgb_label = Gtk.Label()
        rgb_label.set_markup(f'<small>{color[0]}, {color[1]}, {color[2]}</small>')
        rgb_label.set_xalign(0)
        row.append(rgb_label)

        return row

    def on_color_clicked(self, button, index):
        """Handle color button click"""
        # Create color chooser dialog
        dialog = Gtk.ColorDialog()

        # Convert current color to RGBA
        r, g, b = self.palette[index]
        rgba = Gdk.RGBA()
        rgba.red = r / 255.0
        rgba.green = g / 255.0
        rgba.blue = b / 255.0
        rgba.alpha = 1.0

        # Show color chooser
        dialog.choose_rgba(self.get_root(), rgba, None, self.on_color_chosen, index)

    def on_color_chosen(self, dialog, result, index):
        """Handle color chooser result"""
        try:
            rgba = dialog.choose_rgba_finish(result)

            # Convert back to RGB tuple
            r = int(rgba.red * 255)
            g = int(rgba.green * 255)
            b = int(rgba.blue * 255)

            # Update palette
            self.palette[index] = (r, g, b)

            # Update button appearance
            btn, drawing = self.color_buttons[index]
            color = self.palette[index]
            drawing.set_draw_func(lambda area, cr, w, h, col=color:
                                  (cr.set_source_rgb(col[0]/255, col[1]/255, col[2]/255),
                                   cr.rectangle(0, 0, w, h),
                                   cr.fill()))
            drawing.queue_draw()

            # Update RGB label (find it as the 3rd child in parent)
            parent = btn.get_parent()
            child = parent.get_first_child()
            for _ in range(2):  # Skip to RGB label
                child = child.get_next_sibling()
            if child:
                child.set_markup(f'<small>{color[0]}, {color[1]}, {color[2]}</small>')

            # Emit signal
            self.emit('palette-changed', self.palette)

        except Exception as e:
            print(f'Color selection cancelled or error: {e}')

    def on_reset_clicked(self, button):
        """Reset palette to NES default"""
        from chrplunk.chr_format import NES_PALETTE

        self.palette = [tuple(c) for c in NES_PALETTE]

        # Update all buttons
        for i, (btn, drawing) in enumerate(self.color_buttons):
            color = self.palette[i]
            drawing.set_draw_func(lambda area, cr, w, h, col=color:
                                  (cr.set_source_rgb(col[0]/255, col[1]/255, col[2]/255),
                                   cr.rectangle(0, 0, w, h),
                                   cr.fill()))
            drawing.queue_draw()

            # Update RGB label
            parent = btn.get_parent()
            child = parent.get_first_child()
            for _ in range(2):
                child = child.get_next_sibling()
            if child:
                child.set_markup(f'<small>{color[0]}, {color[1]}, {color[2]}</small>')

        # Emit signal
        self.emit('palette-changed', self.palette)

    def get_palette(self):
        """Get current palette"""
        return self.palette
