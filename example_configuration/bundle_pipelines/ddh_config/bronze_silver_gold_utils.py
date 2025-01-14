from copy import deepcopy
from typing import List, Union
from pathlib import Path

from databricks_deployment_helper.models import (
    JobCluster,
    SparkPythonTask,
    AWSClusterNodeType,
    CronSchedule,
    EnvironmentConfiguration,
)
from ddh_config.cluster import BaseCluster
from ddh_config.schedule import default_bronze_schedule
from ddh_config.jobs import CustomizedJob
from ddh_config.tasks import Task, BronzeTask, SilverGoldTask, RetryingTask
from ddh_config.utils import RESOURCES_DIR, SHARED_CONFIG_DIR


def generate_bronze_silver_gold_jobs(
    entity_group: str,
    entity_name: str,
    working_dir: str,
    custom_configs: dict = None,
    to_deploy: Union[bool, EnvironmentConfiguration] = True,
    skip_adhoc_jobs: bool = False,
) -> List[CustomizedJob]:
    """
    Generates bronze, silver and gold jobs for the specified entity.

    Args:
        entity_group (str): The group to which the entity belongs.
        entity_name (str): The name of the entity.
        working_dir (str): The working directory for the job.
        custom_configs (dict, optional): Custom configurations (top-level) for the jobs. Defaults to None.
        skip_adhoc_jobs (dict, optional): Skips returning separate ad_hoc job for each task (layer). Defaults to False.
        to_deploy (Union[bool, EnvironmentConfiguration], optional): Defines if the jobs get deployed at all. Defaults to True.

    Returns:
        List[CustomizedJob]: List of generated jobs.
    """
    custom_configs = custom_configs or {}

    bronze_job = generate_single_task_job(
        layer="bronze",
        entity_group=entity_group,
        entity_name=entity_name,
        working_dir=working_dir,
        custom_config=custom_configs.pop("bronze", {}),
        to_deploy=to_deploy,
    )

    silver_job = generate_single_task_job(
        layer="silver",
        entity_group=entity_group,
        entity_name=entity_name,
        working_dir=working_dir,
        custom_config=custom_configs.pop("silver", {}),
        to_deploy=to_deploy,
    )

    gold_job = generate_single_task_job(
        layer="gold",
        entity_group=entity_group,
        entity_name=entity_name,
        working_dir=working_dir,
        custom_config=custom_configs.pop("gold", {}),
        to_deploy=to_deploy,
    )

    bronze_silver_gold_job = combine_single_task_jobs(
        layer="bronze_silver_gold",
        entity_group=entity_group,
        entity_name=entity_name,
        jobs=[bronze_job, silver_job, gold_job],
        custom_configs=custom_configs,
        to_deploy=to_deploy,
        dependency_mapping={
            gold_job.name.default: [silver_job.name.default],
            silver_job.name.default: [bronze_job.name.default],
            bronze_job.name.default: None,
        },
    )

    if skip_adhoc_jobs:
        return [bronze_silver_gold_job]
    else:
        return [bronze_job, silver_job, gold_job, bronze_silver_gold_job]


def combine_single_task_jobs(
    layer: str,
    entity_group: str,
    entity_name: str,
    jobs: List[CustomizedJob],
    dependency_mapping: dict,
    schedule: Union[EnvironmentConfiguration, CronSchedule] = None,
    custom_configs: dict = None,
    to_deploy: Union[bool, EnvironmentConfiguration] = True,
) -> CustomizedJob:
    """
    Combines multiple single-task jobs (generally ad-hoc jobs) into a multi-task job with explicit dependencies.

    Args:
        layer (str): The layer of the resulting (combined) job.
        entity_group (str): The group to which the entity belongs.
        entity_name (str): The name of the entity.
        jobs (List[CustomizedJob]): The list of jobs that should be combined.
            For a job to be included in the resulting job, it needs to be referenced in the dependency_mapping!
        dependency_mapping (dict): A mapping of explicit task dependencies. Keys and values need to be the job names.
        schedule (Union[EnvironmentConfiguration, CronSchedule], optional): Job schedule. Defaults to `default_bronze_schedule`.
        custom_configs (dict, optional): Custom configurations (job-level) for the resulting job. Defaults to `{}`.
        to_deploy (Union[bool, EnvironmentConfiguration], optional): Defines if the job gets deployed at all. Defaults to True.

    Returns:
        CustomizedJob: Combined multi-task job
    """

    def _get_job_by_name(job_name) -> CustomizedJob:
        return [job for job in jobs if job.name.default == job_name][0]

    custom_configs = custom_configs or {}
    schedule = schedule or default_bronze_schedule

    tasks = []
    job_clusters = []

    for job_name, dependent_job_names in dependency_mapping.items():
        job = _get_job_by_name(job_name)
        task = deepcopy(job.tasks.default[0])
        job_cluster = job.job_clusters.default[0]
        if dependent_job_names:
            dependent_task_keys = [
                _get_job_by_name(dependent_job_name).tasks.default[0].task_key.default
                for dependent_job_name in dependent_job_names
            ]
            task.depends_on = EnvironmentConfiguration(
                default=[{"task_key": dependent_task_key} for dependent_task_key in dependent_task_keys]
            )
        tasks.append(task)
        job_clusters.append(job_cluster)

    # default parameters
    job_parameters = dict(
        name=f"{layer}: {entity_name}".replace("_", " ").title(),
        tags=dict(layer=layer, entity_group=entity_group, entity=entity_name),
        schedule=schedule,
        job_clusters=job_clusters,
        tasks=tasks,
        to_deploy=to_deploy,
    )

    for key, val in custom_configs.items():
        job_parameters[key] = val

    return CustomizedJob(**job_parameters)


def generate_single_task_job(
    layer: str,
    entity_group: str,
    entity_name: str,
    working_dir: str,
    ad_hoc: bool = True,
    custom_config: dict = None,
    schedule: Union[CronSchedule, EnvironmentConfiguration] = None,
    to_deploy: Union[bool, EnvironmentConfiguration] = True,
) -> CustomizedJob:
    """
    Generates a single-task job (ad-hoc by default) for the specified entity.

    Args:
        layer (str): The processing layer of the task.
        entity_group (str): The group to which the entity belongs.
        entity_name (str): The name of the entity.
        working_dir (str): The working directory for the job.
        ad_hoc (bool): Adds the `[Ad-Hoc]` prefix to the job's name. Defaults to True
        custom_config (dict): Custom configuration (job-level) for the job.
        to_deploy (Union[bool, EnvironmentConfiguration], optional): Defines if the job gets deployed at all. Defaults to True.

    Returns:
        CustomizedJob: The generated bronze job.
    """
    custom_config = custom_config or {}

    job_cluster = generate_cluster(
        layer=layer, entity_group=entity_group, entity_name=entity_name, custom_config=custom_config.get("cluster", {})
    )

    task = generate_task(
        layer=layer,
        entity_name=entity_name,
        job_cluster_key=job_cluster.job_cluster_key,
        working_dir=working_dir,
        custom_config=custom_config.get("task", {}),
    )

    job_name = custom_config.get("job_name", f"{layer.capitalize()}: {entity_name.replace('_', ' ').title()}")
    schedule = schedule or custom_config.get("schedule")
    email_notifications = custom_config.get("email_notifications")

    if ad_hoc:
        job_name = f"[Ad-Hoc] {job_name}"
        schedule = None
        email_notifications = None

    return CustomizedJob(
        name=job_name,
        tags=dict(layer=layer, entity_group=entity_group, entity=entity_name),
        tasks=[task],
        **{"email_notifications": email_notifications} if email_notifications else {},
        job_clusters=[job_cluster],
        **{"schedule": schedule} if schedule else {},
        to_deploy=to_deploy,
    )


def generate_task(
    layer: str,
    entity_name: str,
    job_cluster_key: str,
    working_dir: str,
    custom_config: dict,
) -> Task:
    """
    Generates a task for the specified entity and layer.

    Args:
        layer (str): The processing layer of the task.
        entity_name (str): The name of the entity.
        job_cluster_key (str): The key of the cluster associated with the task.
        working_dir (str): The working directory for the task.
        custom_config (dict): Custom configuration (task-level) for the task.

    Returns:
        Task: The generated task.
    """
    # default parameters
    custom_parameters = custom_config.get("custom_parameters", {})
    if layer.lower() == "bronze":
        task_type = BronzeTask
        standard_bronze_config = {
            "--secrets-config-location": f"{SHARED_CONFIG_DIR}/secrets_config.json",
            "--kafka-config-location": f"{SHARED_CONFIG_DIR}/kafka_config.json",
        }
        custom_parameters = merge_custom_parameters(
            standard_parameters=standard_bronze_config, custom_parameters=custom_parameters
        )
    elif layer.lower() in ["silver", "gold"]:
        task_type = SilverGoldTask
        standard_silver_gold_config = {}
        custom_parameters = merge_custom_parameters(
            standard_parameters=standard_silver_gold_config, custom_parameters=custom_parameters
        )
    else:
        task_type = RetryingTask
        standard_config = {}
        custom_parameters = merge_custom_parameters(
            standard_parameters=standard_config, custom_parameters=custom_parameters
        )

    task_parameters = dict(
        task_key=f"{layer}_{entity_name}",
        job_cluster_key=job_cluster_key,
        spark_python_task=SparkPythonTask(
            path=working_dir + "/" + custom_config.get("task_folder", f"task_{layer}"),
            custom_parameters=custom_parameters,
        ),
        depends_on=[],
    )
    # override default parameters with custom config
    for key, val in custom_config.items():
        if key not in ["task_folder", "custom_parameters"]:
            task_parameters[key] = val

    return task_type(**task_parameters)


def generate_cluster(layer: str, entity_group: str, entity_name: str, custom_config: dict) -> JobCluster:
    """
    Generates a standard cluster for the specified entity.

    Args:
        layer (str): The layer of the cluster.
        entity_group (str): The group to which the entity belongs.
        entity_name (str): The name of the entity.
        custom_config (dict): Custom configuration (cluster-level)  for the cluster.

    Returns:
        JobCluster: The generated cluster.
    """
    # default parameters
    new_cluster_parameters = dict(
        custom_tags=dict(layer=layer, entity_group=entity_group, entity=f"{entity_name}"),
        node_type_id=AWSClusterNodeType.GeneralPurpose.m5dn_xlarge,
        number_of_workers=0,
    )

    # override default parameters with custom config
    for key, val in custom_config.items():
        if key not in ["job_cluster_key", "layer"]:
            new_cluster_parameters[key] = val

    new_cluster = BaseCluster(**new_cluster_parameters)
    job_cluster_key = custom_config.get("job_cluster_key", f"cluster_{entity_name}_etl_{layer}")

    return JobCluster(
        job_cluster_key=job_cluster_key,
        new_cluster=new_cluster,
    )


def merge_custom_parameters(
    standard_parameters: dict, custom_parameters: Union[dict, EnvironmentConfiguration]
) -> Union[dict, EnvironmentConfiguration]:
    """
    Merges a dictionary with a dict or EnvironmentConfiguration (of dicts)

    Args:
        standard_parameters (dict): dictionary containing standard parameters to be used for all environments
        custom_parameters (Union[dict, EnvironmentConfiguration]): custom parameters used to update the standard parameters

    Returns:
        dict or EnvironmentConfiguration, depending on the type of custom_parameters
    """
    if isinstance(custom_parameters, EnvironmentConfiguration):
        custom_env_map = {k: {**standard_parameters, **v} for k, v in custom_parameters.environments_map.items()}
        default_parameters = {**standard_parameters, **custom_parameters.default}
        return EnvironmentConfiguration(environments_map=custom_env_map, default=default_parameters)
    elif isinstance(custom_parameters, dict):
        return {**standard_parameters, **custom_parameters}
    else:
        raise TypeError(
            f"custom_parameters must be of type dict or EnvironmentConfiguration, but is of type {type(custom_parameters)}"
        )
