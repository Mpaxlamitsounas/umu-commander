import json
from collections import defaultdict
from json import JSONDecodeError

from configuration import *

_db: defaultdict[str, list[str]]


def init():
    global _db

    if os.path.exists(DB_DIR):
        with open(os.path.join(DB_DIR, DB_NAME), "rt") as db_file:
            try:
                _db = defaultdict(list, json.load(db_file))
            except JSONDecodeError:
                print(f"Could not decode DB file, is it valid JSON?")
                raise JSONDecodeError

    else:
        _db = defaultdict(list)


def write_to_file():
    with open(os.path.join(DB_DIR, DB_NAME), "wt") as db_file:
        # noinspection PyTypeChecker
        json.dump(_db, db_file)


def get():
    return _db


def access(key: str):
    if key in _db:
        return _db[key]


def append_to(key: str, value: str):
    global _db

    if key in _db:
        _db[key].append(value)


def remove_from(key: str, value: str):
    global _db

    if key in _db and value in _db[key]:
        _db[key].remove(value)


def delete(key: str):
    global _db

    if key in _db:
        del _db[key]
