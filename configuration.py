import os
from pathlib import Path

from Classes import DLLOverride

PROTON_DIR: str = os.path.join(Path.home(), ".local/share/Steam/compatibilitytools.d/")
DB_NAME: str = "tracking.json"
DB_DIR: str = PROTON_DIR
CONFIG_NAME: str = "umu-config.toml"
PREFIX_DIR: str = os.path.join(Path.home(), ".local/share/wineprefixes/")
# Label, override string, follow the example
DLL_OVERRIDES_OPTIONS: list[DLLOverride] = [
    DLLOverride("winhttp for BepInEx", "winhttp.dll=n;")
]
