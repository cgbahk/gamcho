from pathlib import Path
import argparse

HYDRA_OUTPUT_DIR = Path("outputs")
assert HYDRA_OUTPUT_DIR.is_dir()

SPECIAL_FILE_NAME = "SPECIAL"


def decorated_print(arg: str):
    byte_size = len(arg)
    print("-" * byte_size)
    print(arg)
    print("-" * byte_size)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--oneline", action="store_true", help="Print first line only")
    args = parser.parse_args()

    for special_path in sorted(HYDRA_OUTPUT_DIR.rglob(f"**/{SPECIAL_FILE_NAME}")):
        if args.oneline:
            print(special_path.parent)
        else:
            decorated_print(str(special_path.parent))
        with open(special_path) as special_file:
            if args.oneline:
                print(special_file.readline())
            else:
                print(special_file.read())
        assert special_path.parents[-2] == HYDRA_OUTPUT_DIR


if __name__ == "__main__":
    main()
