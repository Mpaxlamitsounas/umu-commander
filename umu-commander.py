#!/usr/bin/python3
import json
import os
import subprocess
import sys
from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping, Sequence
from json import JSONDecodeError
from pathlib import Path
from typing import Any

PROTON_DIR: str = os.path.join(Path.home(), ".local/share/Steam/compatibilitytools.d/")
DB_NAME: str = "tracking.json"
DB_PATH: str = os.path.join(PROTON_DIR, DB_NAME)
UMU_CONFIG_NAME: str = "umu-config.toml"
db: defaultdict[str, list[str]]


def print_help():
    print(
        "umu-commander is an interactive CLI tool that helps you manage UMU proton versions, as well as create launch scripts for games."
    )
    print("")
    print(
        f"If your UMU Proton directory is not {PROTON_DIR}, you must change it within the script."
    )
    print(
        "By default, Proton versions will be tracked with a use of a file within the UMU Proton directory named tracking.json, you can change this as well."
    )
    print(
        "If a Proton version is not in the DB file, it will not be removed automatically."
    )
    print("")
    print("umu-commander needs a verb specified after the executable name.")
    print(
        "\ttrack\t- Adds current directory to a Proton version's list of users so that it won't be deleted.\n"
        "\t\t  If the directory is already in a list, the existing entry will be updated accordingly.\n"
        "\t\t  This is also done when using the create verb. If using UMU-Latest directories should be not tracked."
    )
    print("\tuntrack\t- Removes current directory from a Proton version's user list.")
    print("\tmanage\t- Lists users for each Proton version.")
    print("\tcreate\t- Creates a launch script in the current directory.")


def refresh_proton_versions():
    print("Updating UMU Proton.")
    umu_process = subprocess.run(
        ["umu-run", '""'],
        env={"PROTONPATH": "UMU-Latest", "UMU_LOG": "debug"},
        capture_output=True,
        text=True,
    )
    for line in umu_process.stderr.split("\n"):
        if "PROTONPATH" in line and "UMU-Latest" not in line:
            try:
                left: int = line.rfind("/") + 1
                print(f"Using {line[left:len(line) - 1]}.")
            except ValueError:
                print("Could not fetch latest UMU-Proton.")

            break


def get_selection(prompt: str, selection_list: Sequence[str]) -> str:
    selection_list: list[str] = list(selection_list)
    if DB_NAME in selection_list:
        selection_list.remove(DB_NAME)

    while True:
        print(prompt)
        print(
            *[f"{idx}) {label}" for idx, label in enumerate(selection_list, start=1)],
            sep="\n",
        )
        index: str = input("? ")
        print("")
        if index.isdecimal():
            index: int = int(index) - 1
            if index < len(selection_list):
                break

    return selection_list[index]


def format_toml_line(key: str, value: str):
    return f'{key} = ""{value}""\n'


def handle_untrack():
    global db

    current_dir: str = os.getcwd()
    for version, users in db.items():
        if current_dir in users:
            db[version].remove(current_dir)

    print("Directory removed from all user lists.")


def handle_track(version: str = None, refresh_versions: bool = True):
    global db

    if refresh_versions:
        refresh_proton_versions()

    if version is None:
        versions: list[str] = sorted(os.listdir(PROTON_DIR), reverse=True)
        if DB_NAME in versions:
            versions.remove(DB_NAME)
        version: str = get_selection(
            "Select Proton version to add directory as user:", versions
        )

    handle_untrack()
    current_directory: str = os.getcwd()
    db[version].append(current_directory)
    print(
        f"Directory {current_directory} added to Proton version's {version} user list."
    )


def handle_manage(version: str = None):
    if version is None:
        versions = sorted(os.listdir(PROTON_DIR), reverse=True)
        if DB_NAME in versions:
            versions.remove(DB_NAME)

        counts: list[str] = []
        for version in versions:
            counts.append(str(len(db[version])) if version in db else "-")

        while True:
            print("Select Proton version to view user list:")
            print(
                *[
                    f"{idx + 1}) {version} ({count})"
                    for (idx, version), count in zip(enumerate(versions), counts)
                ],
                sep="\n",
            )
            index: str = input("? ")
            print("")
            if index.isdecimal():
                index: int = int(index) - 1
                if index < len(versions):
                    break

        version: str = versions[index]

    if version in db:
        print(f"Directories using {version}:")
        print(*db[version], sep="\n")
    else:
        print("No directories use this version.")


def create_umu_config(params: Mapping[str, str]):
    config: str = "[umu]\n"
    config += format_toml_line("prefix", params["prefix"])
    config += format_toml_line("proton", params["proton"])
    config += format_toml_line("exe", params["exe"])

    config += "launch_args = [\n"
    for arg in params["launch_args"]:
        if arg != "":
            config += f'"{arg}"'
    config += "]\n"

    config_file = open(UMU_CONFIG_NAME, "wt")
    config_file.write(config)
    config_file.close()


def handle_create(
    prefix: str = None,
    proton: str = None,
    dll_overrides: str = None,
    locale: str = None,
    executable_name: str = None,
):
    refresh_proton_versions()

    params: dict[str, str | list[str]] = {"launch_args": []}

    if prefix is None:
        prefix_dir: str = os.path.join(Path.home(), ".local/share/wineprefixes/")

        selection: str = get_selection(
            "Select wine prefix:", ["lidl-64", "lidl-32", "Current directory"]
        )

        if selection == "Current directory":
            params["prefix"] = os.getcwd()
        else:
            params["prefix"] = os.path.join(prefix_dir, selection)

    if proton is None:
        versions: list[str] = [
            "UMU-Latest",
            *sorted(os.listdir(PROTON_DIR), reverse=True),
        ]

        if DB_NAME in versions:
            versions.remove(DB_NAME)
        proton: str = get_selection("Select Proton version:", versions)
    params["proton"] = os.path.join(PROTON_DIR, proton)

    if dll_overrides is None:
        possible_overrides = ["Reset", "Done", "winhttp for BepInEx"]
        selected: set[int] = set()
        while True:
            print("Select DLLs to override, you can select multiple:")
            for idx, label in enumerate(possible_overrides, start=-1):
                if idx in selected:
                    idx = "Y"
                print(f"{idx}) {label}")
            index: str = input("? ")
            print("")

            match index:
                case "-1":
                    selected = set()
                    continue
                case "0":
                    break

            if index.isnumeric():
                index: int = int(index)
                if index - 1 < len(possible_overrides):
                    selected.add(index)

        dll_overrides: str = "WINEDLLOVERRIDES=" if len(selected) > 0 else ""

        for selection in selected:
            match selection:
                case 1:
                    dll_overrides += "winhttp.dll=n;"
    params["launch_args"].append(dll_overrides)

    if locale is None:
        locale: str = "LANG="
        match get_selection("Select locale:", ["Default", "Japanese"]):
            case "Default":
                locale = ""
            case "Japanese":
                locale += "ja_JP.UTF8"
    params["launch_args"].append(locale)

    if executable_name is None:
        files: list[str] = [
            file
            for file in os.listdir(os.getcwd())
            if os.path.isfile(os.path.join(os.getcwd(), file))
        ]
        executable_name: str = get_selection("Select game executable:", files)
    params["exe"] = executable_name

    try:
        create_umu_config(params)
        print(f"Configuration file {UMU_CONFIG_NAME} created at {os.getcwd()}.")
        print(f'Use by running "umu-run --config {UMU_CONFIG_NAME}"')
        if params["proton"] != "UMU-Latest":
            handle_track(proton, False)
    except:
        print("Could not create configuration file.")


def main() -> int:
    global db

    if not os.path.exists(PROTON_DIR):
        print("Proton directory does not exist.")
        return 1

    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rt") as db_file:
            try:
                db = defaultdict(list, json.load(db_file))
            except JSONDecodeError:
                print(f"Could not decode DB file in {DB_PATH}, is it valid JSON?")
                return 3

    else:
        db = defaultdict(list)

    if len(sys.argv) == 1:
        print_help()
        return 0

    verb: str = sys.argv[1]
    match verb:
        case "track":
            handle_track()
        case "untrack":
            handle_untrack()
        case "manage":
            handle_manage()
            return 0
        case "create":
            handle_create()
        case _:
            print("Invalid verb.")
            print_help()
            return 2

    for version, users in db.copy().items():
        if not users and version != sorted(os.listdir(PROTON_DIR), reverse=True)[0]:
            print(f"Proton version {version} has no user directories, remove? (y/n)")
            choice = input().lower()
            if choice == "y":
                # shutil.rmtree(os.path.join(PROTON_DIR, version))
                print(f"Deleted {os.path.join(PROTON_DIR, version)}.\n")
                del db[version]

    with open(DB_PATH, "wt") as db_file:
        # noinspection PyTypeChecker
        json.dump(db, db_file)

    return 0


if __name__ == "__main__":
    exit(main())
