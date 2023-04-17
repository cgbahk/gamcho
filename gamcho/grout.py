"""
grout - library for grouped output directory
"""

from pathlib import Path
from datetime import datetime


def make_dir_grouped_by_datetime(base_dir: Path) -> Path:
    """
    Make and return `base dir / <date> / <time>` directory
    """
    base_dir = Path(base_dir)
    assert base_dir.is_dir()

    now = datetime.now()
    ret = base_dir / now.strftime("%Y-%m-%d") / now.strftime("%H-%M-%S")
    ret.mkdir(parents=True)

    latest_link = base_dir / "1atest"  # Hard-coded link name
    latest_link.unlink(missing_ok=True)
    latest_link.symlink_to(ret)

    return ret
