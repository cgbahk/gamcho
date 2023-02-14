"""
General way to decompress different compress formats
"""
import argparse
from pathlib import Path
from abc import ABC, abstractmethod
import subprocess
import logging
import logging.config

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


class Box(ABC):
    registry = {}

    def __init__(self, box_path: Path):
        self._box_path = Path(box_path)
        assert self._box_path.is_file()

        assert self._is_okay()

    def __init_subclass__(cls, /, key, **kwargs):
        # TODO Deprecate `key`, imply box format from path
        super().__init_subclass__(**kwargs)
        cls.registry[key] = cls

    @abstractmethod
    def _is_okay(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def unbox_to(self, floor_dir: Path):
        raise NotImplementedError


class Zip(Box, key=".zip"):

    def _is_okay(self) -> bool:
        if self._box_path.suffix != ".zip":
            return False

        # TODO Double check with `file` output

        return True

    def unbox_to(self, floor_dir: Path):
        assert is_empty_dir(floor_dir)

        # TODO Use `zipfile` library
        subprocess.run(["unzip", str(self._box_path), "-d", str(floor_dir)], check=True)


class Gz(Box, key=".gz"):

    def _is_okay(self) -> bool:
        suffixes = self._box_path.suffixes

        if suffixes[-1] != ".gz":
            return False

        if len(suffixes) > 1 and suffixes[-2] == ".tar":
            return False

        # TODO Double check with `file` output

        return True

    def unbox_to(self, floor_dir: Path):
        assert is_empty_dir(floor_dir)

        content_path_on_floor = floor_dir / self._box_path.with_suffix("").name

        # TODO Use `gzip` library
        with open(content_path_on_floor, "wb") as content_file:
            subprocess.run(
                ["gzip", "--decompress", "--stdout",
                 str(self._box_path)],
                stdout=content_file,
                check=True,
            )


class Sevenzip(Box, key=".7z"):

    def _is_okay(self) -> bool:
        if self._box_path.suffix != ".7z":
            return False

        # TODO Double check with `file` output

        return True

    def unbox_to(self, floor_dir: Path):
        assert is_empty_dir(floor_dir)

        with py7zr.SevenZipFile(self._box_path) as zip_file:
            zip_file.extractall(floor_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to configuration yaml file")

    config_path = parser.parse_args().config

    with open(config_path) as config_file:
        config = yaml.safe_load(config_file)

    for scenario in config["scenarios"]:
        box_path = Path(scenario["box"])
        floor_dir = Path(scenario["floor"])

        logging.info(f"Unboxing '{box_path}' to '{floor_dir}'")

        assert box_path.is_file()
        assert is_empty_dir(floor_dir)

        box = Box.registry[scenario["suffix"]](box_path)
        box.unbox_to(floor_dir)


if __name__ == "__main__":
    main()
