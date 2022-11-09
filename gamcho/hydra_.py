from hydra.core.hydra_config import HydraConfig
from pathlib import Path


def make_latest_link():
    # TODO Support multirun
    hydra_cfg = HydraConfig.get()
    working_relpath = Path(hydra_cfg.run.dir)

    def access(sequence, index):
        if index >= 0:
            return sequence[index]

        return sequence[len(sequence) + index]

    # Precondition - `working_relpath` is of following format:
    #
    #                  <top_dir> / <job_name> / ...
    #        ~~~~~~~~  ~~~~~~~~~   ~~~~~~~~~~
    # index: -1(as .)         -2           -3
    assert not working_relpath.is_absolute()
    top_working_dir = access(working_relpath.parents, -2)
    job_working_dir = access(working_relpath.parents, -3)
    assert job_working_dir.name == hydra_cfg.job.name

    invoke_dir = Path(hydra_cfg.runtime.cwd)  # TODO Instead use with context for `invoke_dir`

    working_dir = invoke_dir / working_relpath
    assert working_dir.is_dir()

    for directory in (top_working_dir, job_working_dir):
        latest_link = invoke_dir / directory / "1atest"  # Hard-coded link name
        latest_link.unlink(missing_ok=True)
        latest_link.symlink_to(working_dir)
