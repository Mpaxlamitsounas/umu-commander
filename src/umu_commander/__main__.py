import argparse
from argparse import ArgumentParser, Namespace
from json import JSONDecodeError
from pathlib import Path

from InquirerPy.exceptions import InvalidArgument

from umu_commander import VERSION
from umu_commander import configuration as config
from umu_commander import database as db
from umu_commander import tracking, umu_config
from umu_commander.configuration import CONFIG_DIR, CONFIG_NAME, DEFAULT_UMU_CONFIG_NAME
from umu_commander.Types import ExitCode


def init() -> ExitCode:
    try:
        config.load()

    except (JSONDecodeError, KeyError):
        config_path: Path = CONFIG_DIR / CONFIG_NAME
        config_path_old: Path = CONFIG_DIR / (str(CONFIG_NAME) + ".old")

        print(f"Config file at {config_path} could not be read.")

        if not config_path_old.exists():
            print(f"Config file renamed to {config_path_old}.")
            config_path.rename(config_path_old)

        return ExitCode.DECODING_ERROR

    except FileNotFoundError:
        config.dump()

    try:
        db.load()

    except JSONDecodeError:
        db_path: Path = config.DB_DIR / config.DB_NAME
        db_path_old: Path = config.DB_DIR / (str(config.DB_NAME) + ".old")

        print(f"Tracking file at {db_path} could not be read.")

        if not db_path_old.exists():
            db_path.rename(db_path_old)
            print(f"DB file renamed to {db_path_old}.")

    except FileNotFoundError:
        pass

    return ExitCode.SUCCESS


def get_parser_results() -> tuple[ArgumentParser, Namespace]:
    parser = argparse.ArgumentParser(
        prog=f"umu-commander",
        description="Interactive CLI tool to augment umu-launcher",
        epilog="For details, usage, and more, see the README.md file, or visit https://github.com/Mpaxlamitsounas/umu-commander.",
        add_help=True,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
        help="Prints this menu.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppresses all non interactive output.",
    )
    parser.add_argument(
        "verb",
        help="Selects program functionality.",
        choices=["track", "untrack", "users", "delete", "create", "run", "fix"],
    )
    parser.add_argument(
        "-i",
        "--input",
        help=f'Path to file or directory that will be acted upon. Default: $PWD for directories, "{DEFAULT_UMU_CONFIG_NAME}" for files',
        type=Path,
    )
    parser.add_argument(
        "-pr",
        "--proton",
        help="Path to Proton version that will be used. Default: Latest umu proton",
        type=Path,
    )
    parser.add_argument(
        "-wp",
        "--wine-prefix",
        help='Sets the WINE prefix path in config creation. Default: directory/"prefix"',
        type=Path,
        dest="prefix",
    )
    parser.add_argument(
        "-dll",
        "--dll-overrides",
        help="Sets the WINE DLL override string in config creation. Default: No overrides",
    )
    parser.add_argument(
        "-l",
        "--lang",
        help="Sets the language locale override in config creation. Default: No override",
    )
    parser.add_argument(
        "-a",
        "--launch_args",
        help="Sets launch arguments in config creation. Default: No arguments",
    )
    parser.add_argument(
        "-r",
        "--runners",
        help="Sets runners (like MangoHud) in config creation, order matters. Default: No runners",
    )
    parser.add_argument(
        "-o",
        "--output",
        help=f"Sets output config filename in config creation. Default directory/{DEFAULT_UMU_CONFIG_NAME}",
        type=Path,
    )
    parser.add_argument(
        "-ni",
        "--no-interactive",
        help="Uses defaults for missing values instead of prompting.",
        action="store_false",
        dest="interactive",
    )
    parser.add_argument(
        "-nr",
        "--no-refresh",
        "-nu",
        "--no-update",
        help="Do not check for new Proton versions while running.",
        action="store_false",
        dest="refresh",
    )

    args = parser.parse_args()

    return parser, args


def main() -> int:
    if (return_code := init()) != ExitCode.SUCCESS:
        return return_code.value

    parser, args = get_parser_results()

    try:
        match args.verb:
            case "track":
                tracking.track(
                    args.proton,
                    args.input,
                    refresh_versions=args.refresh,
                    quiet=args.quiet,
                )

            case "untrack":
                tracking.untrack(args.input, quiet=args.quiet)

            case "users":
                tracking.users(args.proton)

            case "delete":
                tracking.delete()

            case "create":
                umu_config.create(
                    args.prefix,
                    args.proton,
                    args.dll_overrides,
                    args.lang,
                    args.launch_args,
                    args.runners,
                    args.input,
                    args.output,
                    interactive=args.interactive,
                    refresh_versions=args.refresh,
                    quiet=args.quiet,
                )

            case "run":
                umu_config.run(args.input)

            case "fix":
                umu_config.fix(args.input)

            case _:
                print("Unrecognised verb.")
                parser.print_help()
                return ExitCode.INVALID_SELECTION.value

    except InvalidArgument:
        print("No choices to select from.")
        return ExitCode.INVALID_SELECTION.value

    else:
        return ExitCode.SUCCESS.value

    finally:
        tracking.untrack_unlinked()
        db.dump()


if __name__ == "__main__":
    exit(main())
