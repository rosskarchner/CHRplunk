"""CHR bank selector dialog for NES ROMs"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GObject, GdkPixbuf, GLib
from chrplunk.nes_rom import NESRom
from chrplunk.chr_format import CHRFile, NES_PALETTE


class BankSelectorDialog(Adw.Window):
    """Visual dialog for selecting which CHR bank to open from a NES ROM"""

    __gsignals__ = {
        'bank-selected': (GObject.SignalFlags.RUN_FIRST, None, (int,))
    }

    def __init__(self, parent, rom: NESRom):
        super().__init__()

        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(700, 600)

        self.rom = rom
        self.selected_bank = 0

        # Create header bar
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label='Select CHR ROM Bank'))

        # Cancel button
        cancel_btn = Gtk.Button(label='Cancel')
        cancel_btn.connect('clicked', lambda x: self.close())
        header.pack_start(cancel_btn)

        # Open button
        self.open_btn = Gtk.Button(label='Open Bank')
        self.open_btn.add_css_class('suggested-action')
        self.open_btn.connect('clicked', self.on_open_clicked)
        header.pack_end(self.open_btn)

        # Create toolbar view
        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(header)

        # Create scrolled window for content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        # Create main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content_box.set_margin_start(20)
        content_box.set_margin_end(20)
        content_box.set_margin_top(20)
        content_box.set_margin_bottom(20)

        # ROM info section
        rom_info = rom.get_rom_info()
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        info_title = Gtk.Label()
        info_title.set_markup('<b>ROM Information</b>')
        info_title.set_halign(Gtk.Align.START)
        info_box.append(info_title)

        info_text = (
            f"PRG ROM: {rom_info['prg_banks']} banks ({rom_info['prg_rom_size']} bytes)\n"
            f"CHR ROM: {rom_info['chr_banks']} banks ({rom_info['chr_rom_size']} bytes)\n"
            f"Mapper: {rom_info['mapper']}  •  Mirroring: {rom_info['mirroring']}"
        )
        info_label = Gtk.Label(label=info_text)
        info_label.set_halign(Gtk.Align.START)
        info_label.add_css_class('dim-label')
        info_box.append(info_label)

        content_box.append(info_box)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.append(sep)

        # Banks title
        banks_title = Gtk.Label()
        banks_title.set_markup('<b>Select a Bank</b>')
        banks_title.set_halign(Gtk.Align.START)
        content_box.append(banks_title)

        # Create flow box for bank previews
        flowbox = Gtk.FlowBox()
        flowbox.set_valign(Gtk.Align.START)
        flowbox.set_max_children_per_line(3)
        flowbox.set_min_children_per_line(1)
        flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        flowbox.set_homogeneous(True)
        flowbox.set_column_spacing(10)
        flowbox.set_row_spacing(10)
        flowbox.connect('child-activated', self.on_bank_activated)

        # Create preview for each bank
        for i in range(rom.get_chr_bank_count()):
            bank_card = self.create_bank_card(i)
            flowbox.append(bank_card)

        # Select first bank by default
        flowbox.select_child(flowbox.get_child_at_index(0))

        content_box.append(flowbox)

        scrolled.set_child(content_box)
        toolbar_view.set_content(scrolled)
        self.set_content(toolbar_view)

    def create_bank_card(self, bank_index):
        """Create a visual card for a bank with tile preview"""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.set_size_request(200, 220)

        # Bank title
        title = Gtk.Label()
        title.set_markup(f'<b>Bank {bank_index}</b>')
        title.set_halign(Gtk.Align.CENTER)
        card.append(title)

        # Generate preview image
        try:
            chr_data = self.rom.get_chr_bank(bank_index)
            chr_file = CHRFile.from_bytes(chr_data)

            # Render first 64 tiles (8x8 grid) as preview
            preview_pixbuf = chr_file.render_all_tiles_to_pixbuf(
                tiles_per_row=8,
                scale=2,
                palette=NES_PALETTE
            )

            # Scale down if too large
            if preview_pixbuf.get_width() > 180:
                preview_pixbuf = preview_pixbuf.scale_simple(
                    180,
                    180,
                    GdkPixbuf.InterpType.NEAREST
                )

            picture = Gtk.Picture.new_for_pixbuf(preview_pixbuf)
            picture.set_content_fit(Gtk.ContentFit.CONTAIN)
            picture.set_size_request(180, 180)
            card.append(picture)

        except Exception as e:
            # Fallback if preview generation fails
            error_label = Gtk.Label(label=f'Preview unavailable')
            error_label.add_css_class('dim-label')
            error_label.set_size_request(180, 180)
            card.append(error_label)

        # Info label
        info = Gtk.Label(label=f'8 KB  •  512 tiles')
        info.add_css_class('dim-label')
        card.append(info)

        return card

    def on_bank_activated(self, flowbox, child):
        """Handle bank selection"""
        self.selected_bank = child.get_index()

    def on_open_clicked(self, button):
        """Handle open button click"""
        self.emit('bank-selected', self.selected_bank)
        self.close()


class RomInfoDialog(Adw.MessageDialog):
    """Dialog showing NES ROM information when no CHR ROM is present"""

    def __init__(self, parent, rom: NESRom):
        rom_info = rom.get_rom_info()

        body_text = (
            f"This ROM uses CHR RAM instead of CHR ROM.\n\n"
            f"ROM Information:\n"
            f"• PRG ROM: {rom_info['prg_banks']} banks ({rom_info['prg_rom_size']} bytes)\n"
            f"• CHR ROM: 0 banks (uses CHR RAM)\n"
            f"• Mapper: {rom_info['mapper']}\n"
            f"• Mirroring: {rom_info['mirroring']}\n\n"
            f"CHRplunk can only edit ROMs with CHR ROM data."
        )

        super().__init__(
            transient_for=parent,
            heading='No CHR ROM Data',
            body=body_text
        )

        self.add_response('ok', 'OK')
