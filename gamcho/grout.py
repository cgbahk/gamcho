"""
grout - library for grouped output directory
"""

from pathlib import Path
from datetime import datetime, timezone, timedelta


def make_dir_grouped_by_datetime(base_dir: Path) -> Path:
    """
    Make and return `base dir / <date> / <time>` directory
    """
    base_dir = Path(base_dir)
    assert base_dir.is_dir()

    now = datetime.now(timezone(timedelta(hours=9), "KST"))  # Hard-coded
    ret = base_dir / now.strftime("%Y-%m-%d") / now.strftime("%H-%M-%S")
    ret.mkdir(parents=True)

    latest_link = base_dir / "1atest"  # Hard-coded link name
    latest_link.unlink(missing_ok=True)
    # Use relative link to be more reliable to structure refactoring
    latest_link.symlink_to(ret.relative_to(latest_link.parent))

    return ret
