"""NES Project management system"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum


class Assembler(Enum):
    """Supported assemblers"""
    CA65 = "ca65"
    ASM6 = "asm6"
    NESASM3 = "nesasm3"
    CUSTOM = "custom"


class Mapper(Enum):
    """Common NES mappers"""
    NROM = 0
    MMC1 = 1
    UNROM = 2
    CNROM = 3
    MMC3 = 4
    MMC5 = 5
    CUSTOM = -1


class Mirroring(Enum):
    """Nametable mirroring modes"""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    FOUR_SCREEN = "four_screen"
    SINGLE_SCREEN = "single_screen"


@dataclass
class BuildConfiguration:
    """Build configuration settings"""
    name: str = "Debug"
    assembler: str = Assembler.CA65.value
    assembler_path: str = "ca65"
    linker_path: str = "ld65"
    assembler_flags: List[str] = None
    linker_flags: List[str] = None
    output_filename: str = "game.nes"
    pre_build_script: Optional[str] = None
    post_build_script: Optional[str] = None

    def __post_init__(self):
        if self.assembler_flags is None:
            self.assembler_flags = []
        if self.linker_flags is None:
            self.linker_flags = []


@dataclass
class ROMHeader:
    """NES ROM header configuration"""
    mapper: int = Mapper.NROM.value
    mirroring: str = Mirroring.HORIZONTAL.value
    battery_backed_ram: bool = False
    trainer: bool = False
    four_screen_vram: bool = False
    prg_rom_size: int = 32768  # 32KB default
    chr_rom_size: int = 8192   # 8KB default


@dataclass
class ProjectSettings:
    """Project-wide settings"""
    name: str = "New NES Project"
    version: str = "0.1.0"
    author: str = ""
    description: str = ""

    # Directory structure
    source_dir: str = "source"
    graphics_dir: str = "graphics"
    audio_dir: str = "audio"
    data_dir: str = "data"
    build_dir: str = "build"

    # Default files
    main_source: str = "source/main.s"

    # ROM configuration
    rom_header: Dict[str, Any] = None

    # Build configurations
    build_configs: Dict[str, Dict[str, Any]] = None
    active_config: str = "Debug"

    # Emulator settings
    emulator_path: str = ""
    emulator_args: List[str] = None

    def __post_init__(self):
        if self.rom_header is None:
            self.rom_header = asdict(ROMHeader())
        if self.build_configs is None:
            self.build_configs = {
                "Debug": asdict(BuildConfiguration(name="Debug")),
                "Release": asdict(BuildConfiguration(
                    name="Release",
                    assembler_flags=["-O"],
                    output_filename="game.nes"
                ))
            }
        if self.emulator_args is None:
            self.emulator_args = []


class NESProject:
    """Represents a NES development project"""

    PROJECT_FILE = ".nesproject"
    PROJECT_VERSION = "1.0"

    def __init__(self, root_path: Path, settings: Optional[ProjectSettings] = None):
        """
        Initialize a NES project

        Args:
            root_path: Root directory of the project
            settings: Project settings (None creates defaults)
        """
        self.root_path = Path(root_path)
        self.settings = settings or ProjectSettings()
        self.project_file = self.root_path / self.PROJECT_FILE

    @classmethod
    def create_new(cls, root_path: Path, settings: ProjectSettings,
                   template: str = "empty") -> 'NESProject':
        """
        Create a new NES project

        Args:
            root_path: Where to create the project
            settings: Project settings
            template: Project template to use

        Returns:
            New NESProject instance
        """
        root_path = Path(root_path)
        root_path.mkdir(parents=True, exist_ok=True)

        project = cls(root_path, settings)

        # Create directory structure
        project._create_directories()

        # Create template files
        project._create_template_files(template)

        # Save project file
        project.save()

        return project

    @classmethod
    def load(cls, project_path: Path) -> 'NESProject':
        """
        Load an existing project

        Args:
            project_path: Path to project directory or .nesproject file

        Returns:
            Loaded NESProject instance
        """
        project_path = Path(project_path)

        # If path is a file, assume it's the .nesproject file
        if project_path.is_file():
            project_file = project_path
            root_path = project_path.parent
        else:
            root_path = project_path
            project_file = root_path / cls.PROJECT_FILE

        if not project_file.exists():
            raise FileNotFoundError(f"Project file not found: {project_file}")

        # Load project data
        with open(project_file, 'r') as f:
            data = json.load(f)

        # Validate version
        if data.get('version') != cls.PROJECT_VERSION:
            print(f"Warning: Project version mismatch. Expected {cls.PROJECT_VERSION}, "
                  f"got {data.get('version')}")

        # Create settings from loaded data
        settings_data = data.get('settings', {})
        settings = ProjectSettings(**settings_data)

        return cls(root_path, settings)

    def save(self):
        """Save project to .nesproject file"""
        data = {
            'version': self.PROJECT_VERSION,
            'settings': asdict(self.settings)
        }

        with open(self.project_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _create_directories(self):
        """Create project directory structure"""
        dirs = [
            self.settings.source_dir,
            self.settings.graphics_dir,
            self.settings.audio_dir,
            self.settings.data_dir,
            self.settings.build_dir,
        ]

        for dir_name in dirs:
            dir_path = self.root_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

    def _create_template_files(self, template: str):
        """Create template files based on template type"""
        if template == "empty":
            self._create_empty_template()
        elif template == "hello":
            self._create_hello_template()
        elif template == "platformer":
            self._create_platformer_template()
        else:
            # Default to empty
            self._create_empty_template()

    def _create_empty_template(self):
        """Create minimal empty project files"""
        main_source = self.root_path / self.settings.main_source
        main_source.parent.mkdir(parents=True, exist_ok=True)

        # Create minimal NES assembly file
        content = """; Main source file for {name}
; Assembler: {assembler}

.segment "HEADER"
    .byte "NES", $1A    ; iNES header identifier
    .byte 2             ; 2x 16KB PRG ROM
    .byte 1             ; 1x 8KB CHR ROM
    .byte $01           ; Mapper 0, vertical mirroring
    .byte $00           ; Mapper 0
    .byte 0, 0, 0, 0    ; Padding
    .byte 0, 0, 0, 0

.segment "CODE"
Reset:
    SEI             ; Disable IRQs
    CLD             ; Disable decimal mode

    ; Initialize stack
    LDX #$FF
    TXS

    ; Wait for PPU to be ready
    BIT $2002
:   BIT $2002
    BPL :-

:   BIT $2002
    BPL :-

    ; Main game loop
MainLoop:
    JMP MainLoop

NMI:
    RTI

IRQ:
    RTI

.segment "VECTORS"
    .word NMI
    .word Reset
    .word IRQ

.segment "CHARS"
    ; CHR ROM data would go here
    .res 8192, 0
""".format(name=self.settings.name, assembler=self.settings.build_configs[self.settings.active_config]['assembler'])

        with open(main_source, 'w') as f:
            f.write(content)

        # Create linker config if using ca65
        if self.get_active_build_config()['assembler'] == Assembler.CA65.value:
            self._create_ca65_linker_config()

    def _create_hello_template(self):
        """Create a Hello World template"""
        # For now, same as empty
        # TODO: Add actual Hello World code
        self._create_empty_template()

    def _create_platformer_template(self):
        """Create a platformer game template"""
        # For now, same as empty
        # TODO: Add platformer boilerplate
        self._create_empty_template()

    def _create_ca65_linker_config(self):
        """Create a ca65 linker configuration file"""
        linker_config = self.root_path / self.settings.source_dir / "nes.cfg"

        content = """# NES linker configuration for ca65

MEMORY {
    HEADER: start = $0000, size = $0010, fill = yes, fillval = $00;
    PRG:    start = $8000, size = $8000, fill = yes, fillval = $ff;
    CHR:    start = $0000, size = $2000, fill = yes, fillval = $00;
}

SEGMENTS {
    HEADER:   load = HEADER, type = ro;
    CODE:     load = PRG, type = ro, start = $8000;
    RODATA:   load = PRG, type = ro;
    DATA:     load = PRG, type = rw;
    VECTORS:  load = PRG, type = ro, start = $FFFA;
    CHARS:    load = CHR, type = ro;
}
"""

        with open(linker_config, 'w') as f:
            f.write(content)

    def get_active_build_config(self) -> Dict[str, Any]:
        """Get the active build configuration"""
        return self.settings.build_configs.get(self.settings.active_config, {})

    def get_build_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific build configuration by name"""
        return self.settings.build_configs.get(name)

    def add_build_config(self, config: BuildConfiguration):
        """Add a new build configuration"""
        self.settings.build_configs[config.name] = asdict(config)
        self.save()

    def set_active_config(self, name: str):
        """Set the active build configuration"""
        if name in self.settings.build_configs:
            self.settings.active_config = name
            self.save()
        else:
            raise ValueError(f"Build configuration '{name}' not found")

    def get_source_files(self) -> List[Path]:
        """Get list of all source files in the project"""
        source_dir = self.root_path / self.settings.source_dir
        if not source_dir.exists():
            return []

        # Find all assembly files
        extensions = ['.s', '.asm', '.inc']
        files = []

        for ext in extensions:
            files.extend(source_dir.rglob(f'*{ext}'))

        return sorted(files)

    def get_chr_files(self) -> List[Path]:
        """Get list of all CHR files in the project"""
        graphics_dir = self.root_path / self.settings.graphics_dir
        if not graphics_dir.exists():
            return []

        return sorted(graphics_dir.rglob('*.chr'))

    def get_absolute_path(self, relative_path: str) -> Path:
        """Convert project-relative path to absolute path"""
        return self.root_path / relative_path

    def get_relative_path(self, absolute_path: Path) -> str:
        """Convert absolute path to project-relative path"""
        try:
            return str(Path(absolute_path).relative_to(self.root_path))
        except ValueError:
            # Path is not relative to project root
            return str(absolute_path)
