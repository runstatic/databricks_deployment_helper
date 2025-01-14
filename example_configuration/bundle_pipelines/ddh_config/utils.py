from pathlib import Path
import sys

import git

SHARED_CONFIG_DIR = "/Workspace${workspace.file_path}/shared_config"
RESOURCES_DIR = "/Workspace${workspace.file_path}/resources"


def working_dir_of_current_file(add_dab_file_path: bool = False, workspace_prefix: bool = False) -> str:
    """
    Gets the directory path of the caller's python script
    and adapts it to DAB expected path format.

    Args:
        add_dab_file_path (bool): Whether to add ``${workspace.file_path}`` to the path. This
            variable will be substituted within the DAB deployment.
        workspace_prefix (bool): Whether to prefix the path with ``/Workspace``. This is need
            when accessing files via python (databricks_config.json) but does not work for launching
            the job (pipeline_runner.py).

    Example:
        >>> working_dir_of_current_file(add_dab_file_path=False, workspace_prefix=False)
        jobs/bronze_silver_gold/example_pipeline
        >>>
        >>> working_dir_of_current_file(add_dab_file_path=True, workspace_prefix=False)
        /Users/<service_principal_uuid>/.bundle/files/jobs/bronze_silver_gold/example_pipeline
        >>>
        >>> working_dir_of_current_file(add_dab_file_path=True, workspace_prefix=True)
        /Workspace/Users/<service_principal_uuid>/.bundle/files/jobs/bronze_silver_gold/example_pipeline

    Returns:
        The working directory to be used for databricks asset bundle deployments
    """
    namespace = sys._getframe(1).f_globals  # caller's globals
    calling_script_base_path = Path(namespace["__file__"]).parent  # caller's __file__ base path
    git_working_tree_dir = git.Repo(".", search_parent_directories=True).working_tree_dir
    working_dir = calling_script_base_path.relative_to(git_working_tree_dir)

    if add_dab_file_path:
        working_dir = Path("${workspace.file_path}", working_dir)
    if workspace_prefix:
        working_dir = Path("/Workspace", working_dir)

    return working_dir.as_posix()
