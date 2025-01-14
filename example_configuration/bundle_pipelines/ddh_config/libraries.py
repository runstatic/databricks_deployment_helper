from pathlib import Path
from enum import Enum
import subprocess
from datetime import datetime

import git


YOUR_PROJECT_VERSION = None


class MultipleWheelFilesFound(Exception):
    pass


class WheelFileNotFound(Exception):
    pass


def get_latest_wheel_file(path: str, name: str, expand_to_workspace_path: bool = True) -> str:
    """
    Fetches the latest wheel file containing the given name and returns the path.

    Args:
        path (str): Relative path (from git root) to the folder containing the wheel file
        name (str): Name (or part of it) of the wheel file
        expand_to_workspace_path (bool, optional): Whether to add ``/Workspace`` before the workspace file_path.
            Needs to be disabled for libraries that are defined as an artifact in Databricks.yml. Defaults to True.

    Returns:
        str: Relative path to the wheel file
    """
    git_working_tree_dir = git.Repo(".", search_parent_directories=True).working_tree_dir
    wheel_files = list(Path(git_working_tree_dir, path).glob(f"*{name}*.whl"))
    number_of_wheel_files_found = len(wheel_files)
    if number_of_wheel_files_found == 0:
        raise WheelFileNotFound(f"No wheel file found for name: `{name}` in path: `{path}`")
    if number_of_wheel_files_found > 1:
        raise MultipleWheelFilesFound(
            f"Multiple wheel files ({number_of_wheel_files_found}) found for name: `{name}` in path: `{path}`:"
            f"{wheel_files}"
        )
    file_name = wheel_files[0].name
    if expand_to_workspace_path:
        file_name = f"/Workspace${{workspace.file_path}}/{path}/{file_name}"

    return file_name


def get_latest_YOUR_PROJECT_wheel_file() -> str:
    """
    Appends the current timestamp to the version (only once) to enable the wheel file update on Databricks.

    Returns:
        str: Relative path to the wheel file that will be created when the DAB deployment is called
    """
    global YOUR_PROJECT_VERSION
    # The cached `YOUR_PROJECT_VERSION` ensures that the version is only bumped a single time for a deployment
    if YOUR_PROJECT_VERSION is None:
        # Bumping the version with the current timestamp
        # This is necessary because the DAB won't update a wheel file if the version did not change
        current_version_main = (
            subprocess.run(["poetry", "version", "-s"], capture_output=True)
            .stdout.decode()
            .split("+")[0]
            .replace("\n", "")
        )
        deployment_timestamp = int(datetime.now().timestamp())
        YOUR_PROJECT_VERSION = f"{current_version_main}+{deployment_timestamp}"

        print(
            "Current whl file used: "
            f"dist/YOUR_PROJECT-{YOUR_PROJECT_VERSION}-py3-none-any.whl"
        )
        subprocess.run(["poetry", "version", YOUR_PROJECT_VERSION])

    return f"dist/YOUR_PROJECT-{YOUR_PROJECT_VERSION}-py3-none-any.whl"


class Lib(Enum):
    # pip packages
    databricks_api = {"pypi": {"package": "databricks-api == 0.8.0"}}
    glom = {"pypi": {"package": "glom == 22.1.0"}}
    spooq = {"pypi": {"package": "spooq == 3.3.9"}}
    yaml = {"pypi": {"package": "pyyaml == 6.0"}}
    pika = {"pypi": {"package": "pika == 1.2.1"}}

    # wheel packages
    YOUR_PROJECT = {"whl": get_latest_YOUR_PROJECT_wheel_file()}
    some_other_wheel = {"whl": get_latest_wheel_file(path="example_configuration/dependencies/wheels", name="some_other_wheel")}

    # databricks tests
    chispa = {"pypi": {"package": "chispa == 0.9.2"}}
    pytest = {"pypi": {"package": "pytest == 7.4.0"}}
    pytest_pspec = {"pypi": {"package": "pytest-pspec == 0.0.4"}}
    pytest_mock = {"pypi": {"package": "pytest-mock == 3.6.1"}}


LIBRARIES_BASE = [Lib.YOUR_PROJECT, Lib.glom, Lib.spooq]
LIBRARIES_PUBLISHING = LIBRARIES_BASE + [Lib.pika]

LIBRARIES_BRONZE = LIBRARIES_BASE + [Lib.some_other_wheel, Lib.yaml]
LIBRARIES_SILVER_GOLD = LIBRARIES_BASE

LIBRARIES_DATABRICKS_TESTS = [l for l in Lib]
