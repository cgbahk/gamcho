from pathlib import Path
import subprocess
import argparse
import shlex

import yaml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to configuration yaml file")

    args = parser.parse_args()
    config_yml_path = Path(args.config)
    assert config_yml_path.is_file()

    with open(config_yml_path) as config_file:
        cfg = yaml.safe_load(config_file)

    for instance in cfg["runs"]:
        print(instance["name"])  # TODO logging

        workspace_dir = Path(instance["workspace"])
        workspace_dir.mkdir(parents=True)

        conda_env_dir = Path(instance["conda_env_dir"])
        assert conda_env_dir.is_dir()

        with open(workspace_dir / "conda_list.txt", "w") as conda_list_file:
            subprocess.run(
                shlex.split(f"conda list --prefix {conda_env_dir}"),
                stdout=conda_list_file,
            )

        # TODO Leave GPU info

        converter_path = conda_env_dir / "bin/ct2-fairseq-converter"
        assert converter_path.is_file()

        option = instance["ct2_fairseq_converter_option"]

        command = [str(converter_path)]

        # `output_dir` will be automatically determined in `workspace`
        assert "output_dir" not in option
        command += ["--output_dir", str(workspace_dir / "ct2_model")]

        for key, value in option.items():
            command += [f"--{key}", str(value)]

        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
