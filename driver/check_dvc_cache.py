from pathlib import Path
import argparse
import hashlib


def main():
    parser = argparse.ArgumentParser()

    # TODO Support remote storage path, like ssh or object storage
    parser.add_argument("cache", help="Path to root directory of dvc cache or storage")
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()

    root_dir = Path(args.cache)
    assert root_dir.is_dir()

    for item_path in root_dir.rglob("**/*"):
        if item_path.is_dir():
            continue

        with open(item_path, "rb") as item_file:
            actual_checksum = hashlib.md5(item_file.read()).hexdigest()

        # From documentation:
        #
        # > Note files ... always has exactly one depth level with 2-character directories
        # > (based on hashes of the data contents, ...).
        #
        # https://dvc.org/doc/user-guide/project-structure/internal-files#structure-of-the-cache-directory
        assert item_path.parent.name + item_path.name in (actual_checksum, actual_checksum + ".dir")

        if args.verbose:
            print(f"{actual_checksum} {item_path}")

    print(f"DVC cache '{root_dir}' is okay!")


if __name__ == "__main__":
    main()
