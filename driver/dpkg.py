import sys
import os

from subprocess import check_output
import shlex
from pathlib import Path


def get_package_files(package_name):
    output = check_output(shlex.split(f'dpkg -L {package_name}'))
    return output.decode('utf-8').strip().split('\n')


def is_executable_file(path):
    path = Path(path)

    if path.is_dir():
        return False

    return os.access(path, os.X_OK)


def main():
    assert len(sys.argv) == 2

    package = sys.argv[1]

    pakfiles = get_package_files(package)
    envpaths = os.environ['PATH'].split(':')

    for pakfile in pakfiles:
        if not is_executable_file(pakfile):
            continue

        for envpath in envpaths:
            if Path(pakfile).parent == Path(envpath):
                # TODO Table output
                print(check_output(shlex.split(f'file {pakfile}')).decode('utf-8').strip())
                break


if __name__ == '__main__':
    main()
