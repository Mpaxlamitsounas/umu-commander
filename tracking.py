import shutil

import db
from configuration import *
from util import get_latest_umu, get_selection, refresh_proton_versions


def untrack(quiet: bool = False):
    current_dir: str = os.getcwd()
    for version, users in db.get().items():
        db.remove_from(version, current_dir)

    if not quiet:
        print("Directory removed from all user lists.")


def track(version: str = None, refresh_versions: bool = True, quiet: bool = False):
    if refresh_versions:
        refresh_proton_versions()

    if version is None:
        versions: list[str] = sorted(os.listdir(PROTON_DIR), reverse=True)
        version: str = get_selection(
            "Select Proton version to add directory as user:", versions
        )

    untrack(quiet=True)
    current_directory: str = os.getcwd()
    db.append_to(version, current_directory)

    if not quiet:
        print(
            f"Directory {current_directory} added to Proton version's {version} user list."
        )


def users():
    versions = sorted(os.listdir(PROTON_DIR), reverse=True)

    counts: list[str] = []
    for version in versions:
        counts.append(
            "(" + (str(len(db.access(version))) if version in db.get() else "-") + ")"
        )

    version: str = get_selection(
        "Select Proton version to view user list:", versions, counts
    )

    if version in db.get():
        users: list[str] = db.access(version)
        if len(users) > 0:
            print(f"Directories using {version}:")
            print(*users, sep="\n")
        else:
            print("No directories use this version.")
    else:
        print("This version hasn't been used by umu before.")


def delete():
    latest_umu = get_latest_umu()

    for version, users in db.get().copy().items():
        if version == latest_umu:
            continue

        if len(users) == 0:
            selection: str = input(
                f"{version} has no user directories, delete? (Y/N) ? "
            )
            if selection.lower() == "y":
                shutil.rmtree(os.path.join(PROTON_DIR, version))
                db.delete(version)


def untrack_unlinked():
    for version, users in db.get().copy().items():
        for user in users:
            if not os.path.exists(user):
                db.remove_from(version, user)