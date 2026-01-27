import os
import subprocess
import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import tomli_w
from InquirerPy import inquirer

import umu_commander.configuration as config
from umu_commander import database as db
from umu_commander import tracking
from umu_commander.configuration import (
    DEFAULT_UMU_CONFIG_NAME,
    DLL_OVERRIDES_OPTIONS,
    LANG_OVERRIDES_OPTIONS,
)
from umu_commander.proton import (
    collect_proton_versions,
    get_latest_umu_proton,
    refresh_proton_versions,
)
from umu_commander.Types import Element
from umu_commander.util import build_choices


def select_prefix() -> Path:
    default = Element(str(Path.cwd() / "prefix"), "Current directory")
    choices = build_choices([default, *config.DEFAULT_PREFIX_DIR.iterdir()], None)
    return inquirer.select("Select wine prefix:", choices, default).execute()


def select_proton() -> Path:
    choices = build_choices(None, collect_proton_versions(sort=True))
    return inquirer.select(
        "Select Proton version:", choices, Path.cwd() / "prefix"
    ).execute()


def select_dll_override() -> str:
    choices = build_choices(DLL_OVERRIDES_OPTIONS, None)
    return "".join(
        [
            selection
            for selection in inquirer.checkbox(
                "Select DLLs to override:", choices
            ).execute()
        ]
    )


def select_lang() -> str:
    default = Element("", "No override")
    choices = build_choices([default, *LANG_OVERRIDES_OPTIONS], None)
    return inquirer.select("Select locale:", choices, default).execute()


def set_launch_args() -> list[str]:
    options: str = inquirer.text(
        "Enter executable options, separated by space:"
    ).execute()
    return [opt.strip() for opt in options.split(" ") if opt.strip() != ""]


def set_runners() -> list[str]:
    options: str = inquirer.text(
        "Enter runners in order, separated by space:"
    ).execute()
    return [opt.strip() for opt in options.split(" ") if opt.strip() != ""]


def select_exe() -> Path:
    files = [file for file in Path.cwd().iterdir() if file.is_file()]
    choices = build_choices(files, None)
    return inquirer.select("Select game executable:", choices).execute()


def create(
    prefix: Path = None,
    proton_ver: Path = None,
    dll_overrides: str = None,
    lang: str = None,
    launch_args: Iterable[str] = None,
    runners: Iterable[str] = None,
    exe: Path = None,
    output: Path = None,
    *,
    interactive: bool = True,
    refresh_versions: bool = True,
    quiet: bool = False,
):
    if refresh_versions:
        refresh_proton_versions()

    # Prefix selection
    if prefix is None:
        if interactive:
            prefix = select_prefix()

        else:
            prefix = Path.cwd() / "prefix"

    # Proton selection
    if proton_ver is None:
        if interactive:
            proton_ver = select_proton()

        else:
            proton_ver = get_latest_umu_proton()

    # Select DLL overrides
    if dll_overrides is None and interactive:
        dll_overrides = select_dll_override()

    # Set language locale
    if lang is None and interactive:
        lang = select_lang()

    # Input executable launch args
    if launch_args is None and interactive:
        launch_args = set_launch_args()

    # Set runners for umu-run
    if runners is None and interactive:
        runners = set_runners()

    # Select executable name
    if exe is None:
        exe = select_exe()

    params: dict[str, Any] = {
        "umu": {
            "prefix": str(prefix),
            "proton": str(proton_ver),
            "launch_args": launch_args,
            "runners": runners,
            "exe": str(exe),
        },
        "env": {"WINEDLLOVERRIDES": dll_overrides, "LANG": lang},
    }

    if not params["umu"]["launch_args"]:
        del params["umu"]["launch_args"]

    if not params["env"]["WINEDLLOVERRIDES"]:
        del params["env"]["WINEDLLOVERRIDES"]

    if not params["env"]["LANG"]:
        del params["env"]["LANG"]

    if not params["umu"]["runners"]:
        del params["umu"]["runners"]

    if output is None:
        output = Path.cwd() / DEFAULT_UMU_CONFIG_NAME

    try:
        with open(output, "wb") as file:
            tomli_w.dump(params, file)

    except (ValueError, TypeError):
        if not quiet:
            print("Could not create configuration file.")

    if not quiet:
        print(f"Configuration file {output.name} created in {output.parent}.")
        print(f"Use with umu-commander run.")

    tracking.track(proton_ver, output, refresh_versions=False, quiet=quiet)


def run(umu_config: Path = None):
    if umu_config is None:
        umu_config = Path.cwd() / DEFAULT_UMU_CONFIG_NAME

    if not umu_config.exists():
        print("Specified umu config does not exist.")
        return

    with open(umu_config, "rb") as toml_file:
        toml_conf = tomllib.load(toml_file)

        prefix_path = Path(toml_conf["umu"]["prefix"])
        if not prefix_path.exists():
            prefix_path.mkdir()

        os.environ.update(toml_conf.get("env", {}))
        subprocess.run(
            args=[
                *toml_conf["umu"].get("runners", []),
                "umu-run",
                "--config",
                umu_config,
            ],
            env=os.environ,
        )


def fix(umu_config: Path = None):
    if umu_config is None:
        umu_config = Path.cwd() / DEFAULT_UMU_CONFIG_NAME

    if not umu_config.exists():
        print("Specified umu config does not exist.")
        return

    with open(umu_config, "rb") as toml_file:
        toml_conf = tomllib.load(toml_file)

    base_dir = umu_config.parent
    proton = Path(toml_conf["umu"]["proton"])
    prefix = Path(toml_conf["umu"]["prefix"])
    db.get(proton.parent, proton).append(umu_config)
    if not prefix.exists() and prefix.is_absolute():
        toml_conf["umu"]["prefix"] = str(base_dir / prefix.name)

    exe = Path(toml_conf["umu"]["exe"])
    if not exe.exists() and exe.is_absolute():
        toml_conf["umu"]["exe"] = str(base_dir / exe.name)

    with open(umu_config, "wb") as toml_file:
        tomli_w.dump(toml_conf, toml_file)
