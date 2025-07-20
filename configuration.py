import os
from pathlib import Path

from classes import DLLOverride

PROTON_DIRS: list[str] = [
    os.path.join(Path.home(), ".local/share/Steam/compatibilitytools.d/"),
    os.path.join(Path.home(), ".local/share/umu/compatibilitytools"),
]
DB_NAME: str = "tracking.json"
DB_DIR: str = os.path.join(Path.home(), ".local/share/umu/compatibilitytools")
CONFIG_NAME: str = "umu-config.toml"
PREFIX_DIR: str = os.path.join(Path.home(), ".local/share/wineprefixes/")
# Label, override string, follow the example
DLL_OVERRIDES_OPTIONS: list[DLLOverride] = [
    DLLOverride("winhttp for BepInEx", "winhttp.dll=n;")
]
