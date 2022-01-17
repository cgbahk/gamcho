import argparse
import os

import pandas as pd
import shlex
from pathlib import Path
from subprocess import check_output


def get_package_files(package_name):
    output = check_output(shlex.split(f'dpkg -L {package_name}'))
    return output.decode('utf-8').strip().split('\n')


def is_executable_file(path):
    path = Path(path)

    if path.is_dir():
        return False

    return os.access(path, os.X_OK)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--show-non-path-too', action='store_true')
    parser.add_argument('package')
    args = parser.parse_args()

    pakfiles = get_package_files(args.package)
    envpaths = os.environ['PATH'].split(':')

    def is_in_env_path(path):
        return str(Path(path).parent) in envpaths

    df = pd.DataFrame(pakfiles, columns=['file'])
    df['is_exe'] = df['file'].apply(is_executable_file)
    df['in_PATH'] = df['file'].apply(is_in_env_path)

    df_command = pd.DataFrame()

    if args.show_non_path_too:
        choice = df['is_exe']
    else:
        choice = df['is_exe'] & df['in_PATH']

    df_command['file'] = df.loc[choice]['file']  # TODO reindex

    def get_file_info(path):
        raw_file_info = check_output(shlex.split(f'file {path}')).decode('utf-8').strip()

        prefix = f'{path}: '
        assert raw_file_info.startswith(prefix)

        return raw_file_info[len(prefix):]

    df_command['info'] = df_command['file'].apply(get_file_info)

    print(df_command.to_markdown(index=False))


if __name__ == '__main__':
    main()
