import importlib
import os
import tomllib
from pathlib import Path
from typing import Any

import tomli_w

from umu_commander.Types import Element

CONFIG_DIR: Path = Path.home() / ".config"
CONFIG_NAME: Path = Path("umu-commander.toml")

PROTON_PATHS: tuple[Path, ...] = (
    Path.home() / ".local/share/Steam/compatibilitytools.d",
    Path.home() / ".local/share/umu/compatibilitytools",
    Path.home()
    / ".var/app/com.valvesoftware.Steam/.local/share/Steam/compatibilitytools.d",
)
UMU_PROTON_PATH: Path = Path(Path.home() / ".local/share/Steam/compatibilitytools.d")

DB_NAME: Path = Path("tracking.json")
DB_DIR: Path = Path.home() / ".local/share/umu/compatibilitytools"
DEFAULT_UMU_CONFIG_NAME: Path = Path("umu-config.toml")
DEFAULT_PREFIX_DIR: Path = Path.home() / ".local/share/wineprefixes/"
DLL_OVERRIDES_OPTIONS: tuple[Element, ...] = (
    Element("winhttp.dll=n,b;", "winhttp for BepInEx"),
)
LANG_OVERRIDES_OPTIONS: tuple[Element, ...] = (Element("ja_JP.UTF8", "Japanese"),)
DO_AUTOUPDATE_DEFAULT: bool = True

module = importlib.import_module(__name__)
toml_conf: dict[str, Any] = {}


def load():
    global toml_conf
    with open(os.path.join(CONFIG_DIR, CONFIG_NAME), "rb") as conf_file:
        toml_conf = tomllib.load(conf_file)

        # Proton dirs translation
        setattr(
            module,
            "PROTON_PATHS",
            (Path(proton_dir) for proton_dir in toml_conf["PROTON_PATHS"]),
        )

        # DLL/LANG Override translation
        for key in ["DLL", "LANG"]:
            setattr(
                module,
                f"{key}_OVERRIDES_OPTIONS",
                (
                    Element(value, name)
                    for name, value in toml_conf[f"{key}_OVERRIDES_OPTIONS"].items()
                ),
            )

        for key, value in toml_conf.items():
            if key == "DO_AUTOUPDATE_DEFAULT":
                setattr(module, key, value)

            elif key not in [
                "PROTON_PATHS",
                "DLL_OVERRIDES_OPTIONS",
                "LANG_OVERRIDES_OPTIONS",
            ]:
                setattr(module, key, Path(value))


def _get_attributes() -> dict[str, Any]:
    attributes: dict[str, Any] = {}
    for key in dir(module):
        value = getattr(module, key)
        if not key.startswith("_") and not callable(value) and key.upper() == key:
            attributes[key] = value

    return attributes


def dump():
    if not os.path.exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)

    global toml_conf
    module_conf = _get_attributes()
    del module_conf["CONFIG_DIR"]
    del module_conf["CONFIG_NAME"]

    missing_keys: dict[str, Any] = {}
    for key in set(module_conf.keys()) - set(toml_conf.keys()):
        match key:
            case "PROTON_PATHS":
                missing_keys[key] = [str(proton_dir) for proton_dir in PROTON_PATHS]

            case "DLL_OVERRIDES_OPTIONS" | "LANG_OVERRIDES_OPTIONS":
                missing_keys[key] = {
                    override.name: override for override in getattr(module, key)
                }

            case "DO_AUTOUPDATE_DEFAULT":
                pass

            case _:
                missing_keys[key] = str(module_conf[key])

    if len(missing_keys) != 0 and (CONFIG_DIR / CONFIG_NAME).exists():
        config_path_bak: Path = CONFIG_DIR / (str(CONFIG_NAME) + ".bak")
        if not config_path_bak.exists():
            print(f"Config file renamed to {config_path_bak}.")
            (CONFIG_DIR / CONFIG_NAME).rename(config_path_bak)

        print("Added missing keys to config file.")

    toml_conf.update(missing_keys)
    with open(CONFIG_DIR / CONFIG_NAME, "wb") as conf_file:
        tomli_w.dump(toml_conf, conf_file)
