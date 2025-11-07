"""NES ROM file format parser"""

class NESRomError(Exception):
    """Exception raised for NES ROM parsing errors"""
    pass


class NESRom:
    """Parser for NES ROM files in iNES format

    iNES format structure:
    - 16 byte header
    - Trainer (optional, 512 bytes)
    - PRG ROM data (program code)
    - CHR ROM data (graphics)
    """

    INES_MAGIC = b'NES\x1a'

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.header = None
        self.prg_rom_size = 0  # in bytes
        self.chr_rom_size = 0  # in bytes
        self.has_trainer = False
        self.chr_rom_banks = []  # List of 8KB CHR banks

        self._parse()

    def _parse(self):
        """Parse the NES ROM file"""
        with open(self.filepath, 'rb') as f:
            # Read and validate header
            self.header = f.read(16)

            if len(self.header) < 16:
                raise NESRomError('File too small to be a valid NES ROM')

            if self.header[0:4] != self.INES_MAGIC:
                raise NESRomError('Not a valid iNES ROM file (missing NES header)')

            # Parse header fields
            prg_rom_banks = self.header[4]  # Number of 16KB PRG ROM banks
            chr_rom_banks = self.header[5]  # Number of 8KB CHR ROM banks
            flags6 = self.header[6]
            flags7 = self.header[7]

            self.prg_rom_size = prg_rom_banks * 16384  # 16 KB per bank
            self.chr_rom_size = chr_rom_banks * 8192   # 8 KB per bank
            self.has_trainer = bool(flags6 & 0x04)

            # Skip trainer if present
            if self.has_trainer:
                trainer = f.read(512)
                if len(trainer) < 512:
                    raise NESRomError('Incomplete trainer data')

            # Read PRG ROM
            prg_rom = f.read(self.prg_rom_size)
            if len(prg_rom) < self.prg_rom_size:
                raise NESRomError(f'Incomplete PRG ROM data (expected {self.prg_rom_size}, got {len(prg_rom)})')

            # Read CHR ROM
            if self.chr_rom_size > 0:
                chr_rom = f.read(self.chr_rom_size)
                if len(chr_rom) < self.chr_rom_size:
                    raise NESRomError(f'Incomplete CHR ROM data (expected {self.chr_rom_size}, got {len(chr_rom)})')

                # Split into 8KB banks
                for i in range(chr_rom_banks):
                    bank_start = i * 8192
                    bank_end = bank_start + 8192
                    bank_data = chr_rom[bank_start:bank_end]
                    self.chr_rom_banks.append(bank_data)
            else:
                # ROM uses CHR RAM instead of CHR ROM
                pass

    def has_chr_rom(self) -> bool:
        """Check if ROM contains CHR ROM data"""
        return len(self.chr_rom_banks) > 0

    def get_chr_bank_count(self) -> int:
        """Get number of CHR ROM banks"""
        return len(self.chr_rom_banks)

    def get_chr_bank(self, bank_index: int) -> bytes:
        """Get CHR ROM bank data by index (0-based)"""
        if bank_index < 0 or bank_index >= len(self.chr_rom_banks):
            raise ValueError(f'Invalid CHR bank index: {bank_index}')
        return self.chr_rom_banks[bank_index]

    def get_all_chr_data(self) -> bytes:
        """Get all CHR ROM data concatenated"""
        return b''.join(self.chr_rom_banks)

    def get_rom_info(self) -> dict:
        """Get ROM information as a dictionary"""
        return {
            'prg_rom_size': self.prg_rom_size,
            'chr_rom_size': self.chr_rom_size,
            'prg_banks': self.prg_rom_size // 16384,
            'chr_banks': len(self.chr_rom_banks),
            'has_trainer': self.has_trainer,
            'mapper': ((self.header[6] >> 4) | (self.header[7] & 0xF0)),
            'mirroring': 'Vertical' if (self.header[6] & 0x01) else 'Horizontal',
        }
