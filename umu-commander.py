#!/usr/bin/python3
import sys
from json import JSONDecodeError

import db
import tracking
import umu_config
from configuration import *


def print_help():
    print(
        "umu-commander is an interactive CLI tool to help you manage Proton versions used by umu, as well as create launch configs.",
        "",
        f'If your UMU Proton directory is not "{PROTON_DIR}", you must change it within the configuration.py file.',
        f'What directories each Proton version is being used by is tracked within "{DB_NAME}" in "{DB_DIR}", which is also configurable.',
        "",
        "umu-commander needs one of the following verbs specified after the executable name:",
        "\ttrack\t- Adds the current directory to a specified Proton version's list of users.",
        "\t\t  If the directory is already in another list, it will be removed from it.",
        "\t\t  The create verb will automatically track the current directory.",
        "\t\t  This will not update any existing configs.",
        "\tuntrack\t- Removes the current directory from all tracking lists.",
        "\tusers\t- Lists each Proton version's users.",
        "\tdelete\t- Deletes any Proton version in the tracking database with no users.",
        "\t\t  If a Proton version has not been tracked before, it will not be removed.",
        "\tcreate\t- Creates a custom configuration file in the current directory.",
        f"\trun\t- Uses the config in the current directory to run the program.",
        f"\t\t  This is NOT equivalent to umu-run --config {CONFIG_NAME},",
        "\t\t  as vanilla umu configs do not support setting environment variables",
        sep="\n",
    )


def main() -> int:
    if not os.path.exists(PROTON_DIR):
        print("Proton directory does not exist.")
        return 1

    try:
        db.init()
    except JSONDecodeError:
        return 2

    if len(sys.argv) == 1:
        print_help()
        return 0

    verb: str = sys.argv[1]
    match verb:
        case "track":
            tracking.track()
        case "untrack":
            tracking.untrack()
        case "users":
            tracking.users()
        case "delete":
            tracking.delete()
        case "create":
            umu_config.create()
        case "run":
            umu_config.run()
        case _:
            print("Invalid verb.")
            print_help()
            return 3

    db.write_to_file()

    return 0


if __name__ == "__main__":
    exit(main())
