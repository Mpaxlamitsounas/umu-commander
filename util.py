import re
import subprocess

from configuration import *


def natural_sort_proton_ver_key(s: str, _nsre=re.compile(r"(\d+)")):
    s = s.split("/")[-1]
    return [int(text) if text.isdigit() else text for text in _nsre.split(s)]


def refresh_proton_versions():
    print("Updating umu Proton.")
    umu_update_process = subprocess.run(
        ["umu-run", '""'],
        env={"PROTONPATH": "UMU-Latest", "UMU_LOG": "debug"},
        capture_output=True,
        text=True,
    )
    for line in umu_update_process.stderr.split("\n"):
        if "PROTONPATH" in line and "/" in line:
            try:
                left: int = line.rfind("/") + 1
                print(f"Using {line[left:len(line) - 1]}.")
            except ValueError:
                print("Could not fetch latest UMU-Proton.")

            break


def collect_proton_versions() -> list[str]:
    versions: list[str] = []
    for proton_dir in PROTON_DIRS:
        for proton in os.listdir(proton_dir):
            if proton == DB_NAME:
                continue

            versions.append(os.path.join(proton_dir, proton))

    return versions


def get_selection(
    prompt: str, selection_list: list[str], selection_list_feedback: list[str] = None
) -> str:
    if len(selection_list) == 0:
        print("Nothing to select from.")
        exit(4)

    if selection_list_feedback is None:
        selection_list_feedback = [""] * len(selection_list)

    if DB_NAME in selection_list:
        idx = selection_list.index(DB_NAME)
        selection_list.remove(DB_NAME)
        selection_list_feedback.pop(idx)

    while True:
        print(prompt)
        print(
            *[
                f"{idx}) {label} {feedback}"
                for idx, (label, feedback) in enumerate(
                    zip(selection_list, selection_list_feedback), start=1
                )
            ],
            sep="\n",
        )
        index: str = input("? ")
        print("")
        if index.isdecimal():
            index: int = int(index) - 1
            if index < len(selection_list):
                break

    return selection_list[index]


def get_latest_umu():
    umu_versions = [
        version
        for version in collect_proton_versions()
        if "UMU" in version and version != DB_NAME
    ]
    return sorted(umu_versions, key=natural_sort_proton_ver_key, reverse=True)[0]
