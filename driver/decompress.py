"""
General way to decompress different compress formats
"""
import argparse
from pathlib import Path
from abc import ABC, abstractmethod
import subprocess
import logging
import logging.config
from zipfile import ZipFile

import yaml
import py7zr

logging.config.dictConfig(
    {
        'version': 1,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'default': {
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['default'],
                'level': 'INFO',
            },
        }
    }
)


def is_empty_dir(path: Path):
    path = Path(path)

    if not path.is_dir():
        return False

    return not any(path.iterdir())


class Knife(ABC):
    registry = {}

    def __init_subclass__(cls, /, key, **kwargs):
        # TODO Deprecate `key`, imply box format from path
        super().__init_subclass__(**kwargs)
        cls.registry[key] = cls

    @abstractmethod
    def can_unbox(self, box_path: Path) -> bool:
        raise NotImplementedError

    @abstractmethod
    def unbox(self, box_path: Path, *, floor_dir: Path):
        raise NotImplementedError


class Unzip(Knife, key="unzip"):

    def can_unbox(self, box_path: Path) -> bool:
        if not box_path.is_file():
            return False

        if box_path.suffix != ".zip":
            return False

        # TODO Double check with `file` output

        return True

    def unbox(self, box_path: Path, *, floor_dir: Path):
        assert is_empty_dir(floor_dir)

        # TODO Use `zipfile` library
        subprocess.run(["unzip", str(box_path), "-d", str(floor_dir)], check=True)


class Gzip(Knife, key="gzip"):

    def can_unbox(self, box_path: Path) -> bool:
        if not box_path.is_file():
            return False

        suffixes = box_path.suffixes

        if suffixes[-1] != ".gz":
            return False

        if len(suffixes) > 1 and suffixes[-2] == ".tar":
            return False

        # TODO Double check with `file` output

        return True

    def unbox(self, box_path: Path, *, floor_dir: Path):
        assert is_empty_dir(floor_dir)

        content_path_on_floor = floor_dir / box_path.with_suffix("").name

        # TODO Use `gzip` library
        with open(content_path_on_floor, "wb") as content_file:
            subprocess.run(
                ["gzip", "--decompress", "--stdout",
                 str(box_path)],
                stdout=content_file,
                check=True,
            )


class Py7zr(Knife, key="py7zr"):

    def can_unbox(self, box_path: Path) -> bool:
        if not box_path.is_file():
            return False

        if box_path.suffix != ".7z":
            return False

        # TODO Double check with `file` output

        return True

    def unbox(self, box_path: Path, *, floor_dir: Path):
        assert is_empty_dir(floor_dir)

        with py7zr.SevenZipFile(box_path) as zip_file:
            zip_file.extractall(floor_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to configuration yaml file")

    config_path = parser.parse_args().config

    with open(config_path) as config_file:
        config = yaml.safe_load(config_file)

    for scenario in config["scenarios"]:
        box_path = Path(scenario["box"])

        if "use_auto_floor" in scenario and scenario["use_auto_floor"]:
            floor_dir = Path(str(box_path) + ".content")
            floor_dir.mkdir()
        else:
            floor_dir = Path(scenario["floor"])

        logging.info(f"Unboxing '{box_path}' to '{floor_dir}'")

        assert box_path.is_file()
        assert is_empty_dir(floor_dir)

        knife = Knife.registry[scenario["knife"]]()
        assert knife.can_unbox(box_path)
        knife.unbox(box_path, floor_dir=floor_dir)


if __name__ == "__main__":
    main()
