"""CHR bank selector dialog for NES ROMs"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GObject
from chrplunk.nes_rom import NESRom


class BankSelectorDialog(Adw.MessageDialog):
    """Dialog for selecting which CHR bank to open from a NES ROM"""

    __gsignals__ = {
        'bank-selected': (GObject.SignalFlags.RUN_FIRST, None, (int,))
    }

    def __init__(self, parent, rom: NESRom):
        super().__init__(
            transient_for=parent,
            heading='Select CHR ROM Bank',
            body=f'This ROM contains {rom.get_chr_bank_count()} CHR ROM banks (8 KB each). Select which bank to open:'
        )

        self.rom = rom
        self.selected_bank = 0

        # Add ROM info
        rom_info = rom.get_rom_info()
        info_text = (
            f"\nROM Information:\n"
            f"• PRG ROM: {rom_info['prg_banks']} banks ({rom_info['prg_rom_size']} bytes)\n"
            f"• CHR ROM: {rom_info['chr_banks']} banks ({rom_info['chr_rom_size']} bytes)\n"
            f"• Mapper: {rom_info['mapper']}\n"
            f"• Mirroring: {rom_info['mirroring']}"
        )

        info_label = Gtk.Label(label=info_text)
        info_label.set_wrap(True)
        info_label.set_xalign(0)
        info_label.add_css_class('dim-label')
        info_label.set_margin_top(10)
        info_label.set_margin_bottom(10)

        # Create bank selector
        bank_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bank_box.set_margin_top(10)
        bank_box.set_margin_bottom(10)

        bank_label = Gtk.Label(label='Bank:')
        bank_box.append(bank_label)

        # Create dropdown for bank selection
        bank_list = Gtk.StringList()
        for i in range(rom.get_chr_bank_count()):
            bank_list.append(f'Bank {i}')

        self.bank_dropdown = Gtk.DropDown(model=bank_list)
        self.bank_dropdown.set_selected(0)
        self.bank_dropdown.connect('notify::selected', self.on_bank_changed)
        bank_box.append(self.bank_dropdown)

        # Create main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        content_box.append(info_label)
        content_box.append(bank_box)

        self.set_extra_child(content_box)

        # Add responses
        self.add_response('cancel', 'Cancel')
        self.add_response('open', 'Open')
        self.set_response_appearance('open', Adw.ResponseAppearance.SUGGESTED)
        self.set_default_response('open')

        self.connect('response', self.on_response)

    def on_bank_changed(self, dropdown, _param):
        """Handle bank selection change"""
        self.selected_bank = dropdown.get_selected()

    def on_response(self, dialog, response):
        """Handle dialog response"""
        if response == 'open':
            self.emit('bank-selected', self.selected_bank)


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
