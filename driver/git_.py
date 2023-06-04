import argparse

import pandas as pd
import shlex
from pathlib import Path
from subprocess import check_output


def get_remote_branches_info(repo_dir):
    repo_dir = Path(repo_dir)
    assert repo_dir.is_dir()
    assert (repo_dir / '.git').is_dir()

    def get_remote_branches():
        # TODO Diminish same refs. E.g. `HEAD` usually same with `master`.
        output = check_output(
            shlex.split(f"git branch -r --format='%(refname:short)'"), cwd=repo_dir
        ).decode('utf-8').strip().split('\n')

        return [line.strip() for line in output]

    def get_commit_count(branch_name):
        output = check_output(
            shlex.split(f"git rev-list --count {branch_name}"), cwd=repo_dir
        ).decode('utf-8').strip()

        return int(output)  # FIXME Assert integer

    def get_last_committer_date(branch_name):
        output = check_output(
            shlex.split(f"git log -1 --format=%cr {branch_name}"), cwd=repo_dir
        ).decode('utf-8').strip().split('\n')

        assert len(output) == 1

        return output[0].strip()

    branches = get_remote_branches()

    ret = pd.DataFrame(branches, columns=['branch'])
    ret['commit_count'] = ret['branch'].apply(get_commit_count)
    ret['last_committer_date'] = ret['branch'].apply(get_last_committer_date)

    return ret


def main():
    # TODO Extend functionality using subcommand
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('repo_dir')
    args = parser.parse_args()

    repo_dir = Path(args.repo_dir)
    assert repo_dir.is_dir()
    assert (repo_dir / '.git').is_dir()

    df_branches = get_remote_branches_info(repo_dir)
    assert 'commit_count' in df_branches
    print(
        df_branches.sort_values(by='commit_count', ascending=False, ignore_index=True).to_markdown()
    )


if __name__ == '__main__':
    main()
