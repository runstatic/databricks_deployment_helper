from pathlib import Path

from databricks_deployment_helper.models import (
    JobCluster,
    AWSClusterNodeType,
    EnvironmentConfiguration,
    Env,
    SparkPythonTask,
    Job,
)
from ddh_config.cluster import BaseCluster
from ddh_config.email_notifications import default_email_notifications
from ddh_config.libraries import LIBRARIES_BASE, LIBRARIES_PUBLISHING
from ddh_config.schedule import default_data_service_schedule
from ddh_config.utils import working_dir_of_current_file
from ddh_config.tasks import RetryingTask, Task


# ------------------------------------------------- CLUSTERS -----------------------------------------------------------
custom_tags = dict(layer="complex_pipelines", entity_group="example", entity="multi_task_explicit")

single_node = JobCluster(
    job_cluster_key="single_node",
    new_cluster=BaseCluster(custom_tags=custom_tags),
)

multi_node_small = JobCluster(
    job_cluster_key="multi_node_small",
    new_cluster=BaseCluster(
        node_type_id=AWSClusterNodeType.ComputeOptimized.c5a_4xlarge,
        number_of_workers=2,
        custom_tags=custom_tags,
    ),
)

multi_node_big = JobCluster(
    job_cluster_key="multi_node_big",
    new_cluster=BaseCluster(
        node_type_id=AWSClusterNodeType.ComputeOptimized.c5a_8xlarge,
        number_of_workers=32,
        custom_tags=custom_tags,
    ),
)

# ---------------------------------------------------- JOBS ------------------------------------------------------------
multi_task_explicit_job = Job(
    name="Complex Pipeline: Example Multi Task Explicit",
    tags=custom_tags,
    schedule=EnvironmentConfiguration({Env.DEV: None}, default=default_data_service_schedule),
    email_notifications=default_email_notifications,
    job_clusters=[single_node, multi_node_small, multi_node_big],
    tasks=[
        RetryingTask(
            task_key="loading",
            description=("Does some loading"),
            job_cluster_key="single_node",
            libraries=LIBRARIES_BASE,
            spark_python_task=SparkPythonTask(path=f"{working_dir_of_current_file()}/task_loading"),
        ),
        Task(  # Retrying is too expensive for this task, as the chances are high that it will fail again
            task_key="processing",
            description="Does some processing",
            depends_on=[{"task_key": "loading"}],
            job_cluster_key=EnvironmentConfiguration({Env.PRD: "multi_node_big"}, default="multi_node_small"),
            libraries=LIBRARIES_BASE,
            spark_python_task=SparkPythonTask(
                path=f"{working_dir_of_current_file()}/task_processing",
                custom_parameters=[
                    Path(f"{working_dir_of_current_file()}/task_processing", "extra_file_needed_for_processing.json").as_posix(),
                ],
            ),
        ),
        RetryingTask(
            task_key="zipping",
            description="Does some zipping",
            depends_on=[{"task_key": "processing"}],
            job_cluster_key="multi_node_small",
            libraries=LIBRARIES_BASE,
            spark_python_task=SparkPythonTask(path=f"{working_dir_of_current_file()}/task_zipping"),
        ),
        RetryingTask(
            task_key="deleting",
            description="Does some deleting",
            depends_on=[{"task_key": "zipping"}],
            job_cluster_key="multi_node_small",
            libraries=LIBRARIES_BASE,
            spark_python_task=SparkPythonTask(path=f"{working_dir_of_current_file()}/task_deleting"),
        ),
        RetryingTask(
            task_key="publishing",
            description="Does some publishing",
            depends_on=[{"task_key": "deleting"}],
            job_cluster_key="multi_node_small",
            libraries=LIBRARIES_BASE + LIBRARIES_PUBLISHING,
            spark_python_task=SparkPythonTask(
                path=f"{working_dir_of_current_file()}/task_publishing",
                custom_parameters=[
                    Path(f"{working_dir_of_current_file()}/task_publishing", "configuration_for_publishing_service.json").as_posix(),
                ],
            ),
        ),
    ],
)
