# Script to migrate comment between issue
# It just purely moves comment body content, ignores all others like time written, author, and etc.

import subprocess
import shlex
import json
from pathlib import Path
import click


def shell_output(arg, **kwargs):
    raw = subprocess.check_output(shlex.split(arg), **kwargs)
    return raw.decode('utf-8')


def shell(arg, **kwargs):
    if "check" not in kwargs:
        kwargs["check"] = True

    subprocess.run(shlex.split(arg), **kwargs)


@click.group()
def cli():
    pass


@cli.command()
@click.option("--repo", required=True, help="[IN] ORG/REPO")
@click.option("--issue", required=True, help="[IN] Issue number")
@click.option("--comments-json", default="/dev/stdout", help="[OUT] Path to dump comments as json")
def get_all_comments(repo, issue, comments_json):
    comments_json_path = Path(comments_json)

    full_comments_str = shell_output(f"gh api repos/{repo}/issues/{issue}/comments --paginate")
    full_comments = json.loads(full_comments_str)

    # Let's summarize
    summ_comments = []
    summ_keys = ["id", "url", "html_url", "body"]

    for full_comment in full_comments:
        summ_comments.append({summ_key: full_comment[summ_key] for summ_key in summ_keys})

    with open(comments_json_path, 'w') as comments_json_file:
        json.dump(summ_comments, comments_json_file, indent=2)


@cli.command()
@click.option("--target-repo", required=True, help="[IN] ORG/REPO")
@click.option(
    "--target-issue",
    required=True,
    help="[IN] New issue comments will be created in this target issue number"
)
@click.option("--comments-json", help="[IN] Path to comments info to be migrated")
def migrate_comments(target_repo, target_issue, comments_json):
    """
    TODO Check reference usage for migrated comments
    """
    comments_json_path = Path(comments_json)
    assert comments_json_path.is_file()

    with open(comments_json_path) as comments_json_file:
        comments = json.load(comments_json_file)

    tmp_body_path = Path("/tmp/migrate.issue.comment.body.txt")

    for comment in comments:
        with open(tmp_body_path, "w") as body_file:
            body_file.write(comment["body"])

        shell(f"gh issue comment --repo {target_repo} --body-file {tmp_body_path} {target_issue}")

        # TODO Might be safer to check deleted comment by user
        # Using `shell_output` as calliing `shell` here requires user input
        print(shell_output(f"gh api --method DELETE {comment['url']}"))

    tmp_body_path.unlink()  # TODO try/finally


if __name__ == "__main__":
    cli()
