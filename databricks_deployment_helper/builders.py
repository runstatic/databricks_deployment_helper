from pathlib import Path
from typing import List, Dict

import yaml

from databricks_deployment_helper.models.env import (
    Env,
)
from databricks_deployment_helper.models.job import Job


def set_task_new_cluster_from_job_clusters(job: dict):
    """
    Removes job_clusters by putting the job cluster definition inside the task.

    Args:
        job: resolved Job as dictionary

    Returns:
        job dictionary without job clusters
    """
    if (job_clusters := job.get("job_clusters")) is not None:
        job_clusters_dict = {job_cluster["job_cluster_key"]: job_cluster["new_cluster"] for job_cluster in job_clusters}
        for task in job.get("tasks", []):
            if (job_cluster_key := task.get("job_cluster_key")) is not None:
                task["new_cluster"] = job_clusters_dict[job_cluster_key]
                del task["job_cluster_key"]
        del job["job_clusters"]
    return job


def build_dbx_deployment_file(environments: List[Env], jobs_to_deploy: List[Job], assets_only: bool = False) -> Dict:
    """
    Builds the dictionary in the DBX deployment file format.

    Args:
        environments: list of databricks environments
        jobs_to_deploy: list of jobs to be deployed
        assets_only: boolean value indicating if the deployment file are intended to be used with dbx assets_only option.
                     deployment configuration for dbx's assets_only option do not have shared job clusters
                     if a task use a cluster defined in job_clusters, the cluster definition will be moved inside
                     the task.

    Returns:
        DBX deployment python dictionary
    """
    main_deployment_dict = {"environments": {}}
    for env in environments:
        jobs = [job.resolve(env) for job in jobs_to_deploy if job.to_deploy.resolve(env)]
        if assets_only:
            jobs = list(map(set_task_new_cluster_from_job_clusters, jobs))
        if jobs:
            main_deployment_dict["environments"][env.value.upper()] = {"workflows": jobs}
    return main_deployment_dict


class YamlVerboseDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        # Disables yaml anchors
        return True


def generate_dab_deployment_file(
    environment: Env,
    jobs_to_deploy: List[Job],
    output_file: str = "dab_deployment_generated_by_ddh.yml",
    head_rows: int = 15,
):
    """
    Generates and writes a YAML file containing the provided job definitions for a single environment.

    Args:
        environment: Databricks environment for the deployment
        jobs_to_deploy: List of jobs to be deployed
        output_file: Name of the output file
        head_rows: Number of lines to print (preview) to console after writing the deployment file

    """
    print(f"Generating DAB deployment file for '{environment.name}' ...")
    output_dict = {
        "resources": {
            "jobs": {
                job.resolve(environment)["name"]
                .replace((" "), "_")
                .replace((":"), "")
                .replace(("["), "_")
                .replace(("]"), "_")
                .lower(): job.resolve(environment)
                for job in jobs_to_deploy
                if job.to_deploy.resolve(environment)
            }
        }
    }

    output_file_path = Path(output_file).absolute().as_posix()
    print(f"Writing DAB deployment file to '{output_file_path}' ...")
    with open(output_file_path, "w") as file_handle:
        yaml.dump(output_dict, file_handle, Dumper=YamlVerboseDumper)

    print("Output file successfully written.")
    if head_rows and int(head_rows) > 0:
        print("")
        print("\n".join(yaml.dump(output_dict).split("\n")[: int(head_rows)]))
        print("...\n")

    print(
        f"To deploy this file please run \ndatabricks bundle deploy --target <your asset bundle target> [-p <your databricks-cli profile]"
    )
