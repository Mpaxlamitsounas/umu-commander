import re
import subprocess

from classes import Group
from configuration import *


def natural_sort_proton_ver_key(e: Element, _nsre=re.compile(r"(\d+)")):
    s: str = e.value
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


def _sort_proton_versions(versions: list[Element]) -> list[Element]:
    return sorted(versions, key=natural_sort_proton_ver_key, reverse=True)


def collect_proton_versions(sort: bool = False) -> list[Group]:
    version_groups: list[Group] = []
    for proton_dir in PROTON_DIRS:
        versions: list[Element] = [
            Element(proton_dir, version, "")
            for version in os.listdir(proton_dir)
            if version != DB_NAME
        ]
        if sort:
            versions = sorted(versions, key=natural_sort_proton_ver_key, reverse=True)

        version_groups.append(
            Group(proton_dir, f"Proton versions in {proton_dir}:", versions)
        )

    return version_groups


def get_latest_umu_proton():
    umu_proton_versions: list[Element] = [
        Element(UMU_PROTON_DIR, version, "")
        for version in os.listdir(UMU_PROTON_DIR)
        if "UMU" in version and version != DB_NAME
    ]

    return sorted(umu_proton_versions, key=natural_sort_proton_ver_key, reverse=True)[
        0
    ].version_num


def values_to_elements(values: list[str]) -> list[Element]:
    return [Element(value=value) for value in values]


def _print_selection_group(
    elements: list[Element], enum_start_idx: int, tab: bool = True
):
    prefix: str = "\t" if tab else ""
    print(
        *[
            f"{prefix}{idx}) {element.value} {element.info}"
            for idx, element in enumerate(elements, start=enum_start_idx)
        ],
        sep="\n",
    )
    print("")


def _translate_index_to_selection(
    selection_index: int,
    selection_elements: list[Element],
    selection_groups: list[Group],
) -> Element:
    len_counter: int = 0

    if selection_elements is not None:
        selection_groups.insert(0, Group("", "", selection_elements))

    for group in selection_groups:
        len_counter += len(group.elements)
        if len_counter > selection_index:
            break

    return Element(
        group.identity, group.elements[selection_index - len_counter].value, ""
    )


def get_selection(
    prompt: str,
    selection_elements: list[Element] | None,
    selection_groups: list[Group] | None,
) -> Element:
    if selection_groups is None:
        selection_groups = []

    if len(selection_elements) == 0 and (
        len(selection_groups) == 0
        or all([len(group.elements) == 0 for group in selection_groups])
    ):
        print("Nothing to select from.")
        exit(4)

    while True:
        enum_start_idx: int = 1

        print(prompt)

        if selection_elements is not None:
            _print_selection_group(selection_elements, enum_start_idx, tab=False)
            enum_start_idx += len(selection_elements)

        for group_idx, group in enumerate(selection_groups):
            if len(group.elements) == 0:
                continue

            print(group.label)
            _print_selection_group(group.elements, enum_start_idx)

            enum_start_idx += len(group.elements)

        selection_index: str = input("? ")
        print("")
        if selection_index.isdecimal():
            selection_index: int = int(selection_index) - 1
            if enum_start_idx - 1 > selection_index >= 0:
                break

    return _translate_index_to_selection(
        selection_index, selection_elements, selection_groups
    )
