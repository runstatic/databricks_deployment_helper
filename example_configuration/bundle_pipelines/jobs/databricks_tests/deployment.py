from databricks_deployment_helper.models import (
    JobCluster,
    SparkPythonTask,
    Job,
)
from ddh_config.cluster import BaseCluster
from ddh_config.libraries import LIBRARIES_DATABRICKS_TESTS
from ddh_config.utils import working_dir_of_current_file
from ddh_config.tasks import Task


# ------------------------------------------------- CLUSTERS -----------------------------------------------------------
custom_tags = dict(layer="testing", entity="integration_tests")

single_node = JobCluster(
    job_cluster_key="single_node",
    new_cluster=BaseCluster(
        custom_tags=custom_tags,
    ),
)

# ---------------------------------------------------- JOBS ------------------------------------------------------------
databricks_tests = Job(
    name="Databricks Tests",
    tags=custom_tags,
    job_clusters=[single_node],
    tasks=[
        Task(
            task_key="integration_tests",
            description="runs the integration tests",
            libraries=LIBRARIES_DATABRICKS_TESTS,
            job_cluster_key="single_node",
            spark_python_task=SparkPythonTask(
                path=f"{working_dir_of_current_file()}/task_integration_tests",
                custom_parameters=["/Workspace${workspace.file_path}/tests/databricks/integration"],  # path to your python test files to be executed by pytest
            ),
        )
    ],
)
