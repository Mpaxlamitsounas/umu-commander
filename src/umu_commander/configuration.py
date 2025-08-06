import os
import tomllib
from pathlib import Path

import tomli_w

from umu_commander.classes import DLLOverride

_CONFIG_DIR: str = os.path.join(Path.home(), ".config")
_CONFIG_NAME: str = "umu-commander.toml"


PROTON_PATHS: tuple[str, ...] = (
    os.path.join(Path.home(), ".local/share/Steam/compatibilitytools.d/"),
    os.path.join(Path.home(), ".local/share/umu/compatibilitytools"),
)
UMU_PROTON_PATH: str = os.path.join(
    Path.home(), ".local/share/Steam/compatibilitytools.d/"
)
DB_NAME: str = "tracking.json"
DB_DIR: str = os.path.join(Path.home(), ".local/share/umu/compatibilitytools")
UMU_CONFIG_NAME: str = "umu-config.toml"
DEFAULT_PREFIX_DIR: str = os.path.join(Path.home(), ".local/share/wineprefixes/")
DLL_OVERRIDES_OPTIONS: tuple[DLLOverride, ...] = (
    DLLOverride("winhttp for BepInEx", "winhttp.dll=n;"),
)


def load():
    if not os.path.exists(os.path.join(_CONFIG_DIR, _CONFIG_NAME)):
        return

    with open(os.path.join(_CONFIG_DIR, _CONFIG_NAME), "rb") as conf_file:
        toml_conf = tomllib.load(conf_file)
        if "DLL_OVERRIDES_OPTIONS" in toml_conf:
            toml_conf["DLL_OVERRIDES_OPTIONS"] = tuple(
                [
                    DLLOverride(label, override_str)
                    for label, override_str in toml_conf[
                        "DLL_OVERRIDES_OPTIONS"
                    ].items()
                ]
            )

        module = __import__(__name__)
        for key, value in toml_conf.items():
            setattr(module, key, value)


def _get_attributes():
    module = __import__(__name__)
    attributes = {}
    for key in dir(module):
        value = getattr(module, key)
        if not key.startswith("_") and not callable(value) and key.upper() == key:
            attributes[key] = value

    return attributes


def dump():
    if not os.path.exists(_CONFIG_DIR):
        os.mkdir(_CONFIG_DIR)

    with open(os.path.join(_CONFIG_DIR, _CONFIG_NAME), "wb") as conf_file:
        toml_conf = _get_attributes()
        toml_conf["DLL_OVERRIDES_OPTIONS"] = dict(
            [(override.info, override.value) for override in DLL_OVERRIDES_OPTIONS]
        )

        tomli_w.dump(toml_conf, conf_file)
