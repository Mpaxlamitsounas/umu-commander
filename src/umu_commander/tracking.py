import shutil
from pathlib import Path

from InquirerPy import inquirer

import umu_commander.database as db
from umu_commander.configuration import DEFAULT_UMU_CONFIG_NAME
from umu_commander.proton import (
    collect_proton_versions,
    get_latest_umu_proton,
    update_proton_versions,
)
from umu_commander.util import (
    build_choices,
)


def select_config() -> str:
    files = [file for file in Path.cwd().iterdir() if file.is_file()]
    choices = build_choices(files, None)
    return inquirer.select("Select umu-commander config:", choices).execute()


def untrack(target_dir: Path = None, *, quiet: bool = False):
    if target_dir is None:
        target_dir = Path.cwd()

    target_dir = target_dir.absolute()

    for proton_dir in db.get().keys():
        for proton_ver in db.get(proton_dir):
            if target_dir in db.get(proton_dir, proton_ver):
                db.get(proton_dir, proton_ver).remove(target_dir)

    if not quiet:
        print("Config removed from all tracking lists.")


def track(
    proton_ver: Path = None,
    config: Path = None,
    *,
    interactive: bool = True,
    update_versions: bool = True,
    quiet: bool = False,
):
    if config is None:
        if interactive:
            config = select_config()

        else:
            config = Path.cwd() / DEFAULT_UMU_CONFIG_NAME

    if update_versions:
        update_proton_versions()

    if proton_ver is None:
        proton_dirs = collect_proton_versions(sort=True)
        choices = build_choices(None, proton_dirs)
        proton_ver: Path = inquirer.select(
            "Select Proton version to track config with:", choices
        ).execute()

    proton_ver = proton_ver.absolute()
    config = config.absolute()

    untrack(config, quiet=True)
    db.get(proton_ver.parent, proton_ver).append(config)

    if not quiet:
        print(
            f"Config {config} added to Proton version's {proton_ver.name} in {proton_ver.parent} tracking list."
        )


def users(proton_ver: Path = None):
    if proton_ver is None:
        proton_dirs = collect_proton_versions(sort=True)
        choices = build_choices(None, proton_dirs, count_elements=True)
        proton_ver: Path = inquirer.select(
            "Select Proton version to view user list:", choices
        ).execute()

    proton_ver = proton_ver.absolute()

    if proton_ver.parent in db.get() and proton_ver in db.get(proton_ver.parent):
        version_users: list[Path] = db.get(proton_ver.parent, proton_ver)
        if len(version_users) > 0:
            print(
                f"Directories tracked by {proton_ver.name} of {proton_ver.parent}:",
                *version_users,
                sep="\n\t",
            )

        else:
            print("This version is tracking no configs.")

    else:
        print("This version hasn't been used by umu before.")


def delete():
    for proton_dir in db.get().keys():
        for proton_ver, version_users in db.get(proton_dir).copy().items():
            if proton_ver == get_latest_umu_proton():
                continue

            if len(version_users) == 0:
                confirmed: bool = inquirer.confirm(
                    f"Version {proton_ver.name} in {proton_dir} is tracking no directories, delete?"
                ).execute()
                if confirmed:
                    try:
                        shutil.rmtree(proton_dir / proton_ver)
                    except FileNotFoundError:
                        pass
                    del db.get(proton_dir)[proton_ver]


def untrack_unlinked():
    for proton_dir in db.get().keys():
        for proton_ver, version_users in db.get()[proton_dir].items():
            for user in version_users:
                if not user.exists():
                    db.get(proton_dir, proton_ver).remove(user)
