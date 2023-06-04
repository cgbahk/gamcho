# TODO Parallelize
from pathlib import Path
import hashlib
import tempfile
import logging
import re
from typing import Dict
import os
import argparse

import huggingface_hub
import git
from tqdm import tqdm

DEFAULT_CACHE_DIR = "~/.cache/huggingface/hub"


def git_repo_clone_with_retry(*args, **kwargs):
    for _ in range(100):  # Hard-coded
        try:
            return git.Repo.clone_from(*args, **kwargs)
        except git.GitCommandError as err:
            if b"gnutls_handshake" not in err.args[2]:
                raise err

    assert False  # All retry failed, must be some other issue


class ChecksumCache:

    def __init__(self):
        self._real_full_path_to_sha256 = {}

    def get_checksum(self, path: Path) -> Dict:
        assert Path(path).is_file()

        real_full_path = os.path.realpath(path)

        if real_full_path in self._real_full_path_to_sha256:
            # Cache hit
            return {
                "checksum": self._real_full_path_to_sha256[real_full_path],
                "cost_in_byte": 0,
            }

        checksum = compute_sha256(real_full_path)
        self._real_full_path_to_sha256[real_full_path] = checksum

        return {
            "checksum": checksum,
            "cost_in_byte": Path(real_full_path).stat().st_size,
        }


def compute_sha256(path: Path):
    assert Path(path).is_file()

    ret = hashlib.sha256()

    with open(path, "rb") as f:
        # TODO Chunk size hard-coded, try optimal value for big file
        # TODO Update `progress_bar` here
        for chunk in iter(lambda: f.read(4096), b""):
            ret.update(chunk)

    return ret.hexdigest()


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--cache-dir",
        default=DEFAULT_CACHE_DIR,
        help="Huggingface model cache directory",
    )
    args = parser.parse_args()
    assert Path(args.cache_dir).expanduser().is_dir()

    info = huggingface_hub.scan_cache_dir(args.cache_dir)
    # info.size_on_disk

    for warning in info.warnings:
        logging.warning(f"{type(warning).__name__}: {warning}")
    # NOTE `total` is not accurate, as some files maybe checked duplicated with multiple revisions
    progress_bar = tqdm(
        unit="GB",
        total=info.size_on_disk / 1000**3,
        smoothing=0,
    )

    checksum_cache = ChecksumCache()

    for repo_info in info.repos:
        logging.debug(f"{repo_info.repo_id=}")

        git_url = f"https://huggingface.co/{repo_info.repo_id}"

        for revision in repo_info.revisions:
            logging.debug(f"{revision.commit_hash=}")

            with tempfile.TemporaryDirectory() as repo_dir:
                repo = git_repo_clone_with_retry(
                    url=git_url,
                    to_path=repo_dir,
                    env={"GIT_LFS_SKIP_SMUDGE": "1"},
                )

                repo.git.reset("--hard", revision.commit_hash)
                lfs_file_paths = repo.git.lfs("ls-files", "--name-only").splitlines()

                for file in revision.files:
                    actual_path = file.file_path
                    checksum_result = checksum_cache.get_checksum(actual_path)

                    actual_checksum = checksum_result["checksum"]
                    progress_bar.update(checksum_result["cost_in_byte"] / 1000**3)

                    logging.debug(f"{actual_path=}")
                    logging.debug(f"{actual_checksum=}")

                    relative_path = actual_path.relative_to(revision.snapshot_path)
                    cloned_path = repo_dir / relative_path
                    assert cloned_path.is_file()

                    if str(relative_path) in lfs_file_paths:
                        with open(cloned_path) as cloned_file:
                            first_line = cloned_file.readline()
                            assert "https://git-lfs.github.com" in first_line

                            second_line = cloned_file.readline()
                            expected_checksum = re.fullmatch("oid sha256:(.*)\n", second_line) \
                                .group(1)
                    else:
                        # NOTE This is not counted in `progress_bar`, as it determined on runtime.
                        # Guess effect of this is small, most big file mostly covered by git-lfs
                        expected_checksum = compute_sha256(cloned_path)

                    if expected_checksum != actual_checksum:
                        logging.error(
                            " ".join(
                                [
                                    f"Checksum mismatch for {actual_path}:",
                                    f"expected {expected_checksum[:10]}",
                                    f"actually {actual_checksum[:10]}",
                                ]
                            )
                        )


if __name__ == "__main__":
    main()
