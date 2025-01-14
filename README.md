**This library is no longer under active development!**

This library was developed by the Data Engineering team at Runtastic in Austria.
We decided to open source this library as the code is generic enough to be useful for any company using the databricks scheduler.

# databricks-deployment-helper

A set of python classes to define databricks job according to the [Jobs API 2.1](https://docs.databricks.com/dev-tools/api/latest/jobs.html#).

## Usage

1. Create a job object using the models provided in the module `models` and from company customized configs (named `ddh_config` in the example_configuration).

### Explicit clusters and tasks

```py
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
    new_cluster=BaseCluster(  # Base cluster with some defaults set by your ddh_config
        custom_tags=custom_tags,
    ),
)

# ---------------------------------------------------- JOBS ------------------------------------------------------------
databricks_tests = Job(
    name="Databricks Tests",
    email_notifications=EnvironmentConfiguration(  # Special configuration that is environment dependend
        environments_map={Env.PRE: EmailNotification(on_failure=["pre@example.com"])},
        default=None,
    ),
    tags=custom_tags,
    job_clusters=[single_node],
    tasks=[
        Task(
            task_key="integration_tests",
            description="runs the integration tests",
            libraries=LIBRARIES_DATABRICKS_TESTS,
            job_cluster_key="single_node",
            spark_python_task=SparkPythonTask(
                # Special task that assumes a ``pipeline_runner.py`` and a ``databricks_config.json`` to be present in
                # the task subfolder (`path`).
                path=f"{working_dir_of_current_file()}/task_integration_tests",
                # Custom parameters are for additional parameters, aside from the above mentioned.
                custom_parameters=["/Workspace${workspace.file_path}/tests/databricks/integration"],  # path to your python test files to be executed by pytest
            ),
        )
    ],
)
```

### Bronze, Silver, Gold and Ah-Hoc jobs via helper method

```py
from ddh_config.utils import working_dir_of_current_file
from ddh_config.bronze_silver_gold_utils import generate_bronze_silver_gold_jobs
from databricks_deployment_helper.models.env import Env
from databricks_deployment_helper.models.environment_configuration import EnvironmentConfiguration
from databricks_deployment_helper.models.cluster_node_types_aws import AWSClusterNodeType


# --------------------------------------------- NON-STANDARD CONFIG ---------------------------------------------------
custom_configs = {
    "silver": {
        "cluster": {
            "node_type_id": EnvironmentConfiguration(
                environments_map={Env.STG: AWSClusterNodeType.ComputeOptimized.c5a_xlarge},
                default=AWSClusterNodeType.ComputeOptimized.c5a_2xlarge,
            )
        }
    },
    "gold": {
        "cluster": {
            "node_type_id": EnvironmentConfiguration(
                environments_map={Env.STG: AWSClusterNodeType.ComputeOptimized.c5a_xlarge},
                default=AWSClusterNodeType.ComputeOptimized.c5a_4xlarge,
            )
        }
    },
}
# ----------------------------------------------- GENERATE JOBS --------------------------------------------------------

jobs = generate_bronze_silver_gold_jobs(
    entity_group="bronze_silver_gold_example",
    entity_name="simple",
    working_dir=working_dir_of_current_file(),
    custom_configs=custom_configs,
)
```

2. Use a builder

### Databricks Asset Bundle (DAB)

```py
from jobs.databricks_tests.deployment import databricks_tests

env = Env.DEV

jobs = [databricks_tests]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", "--output-file", default="dab_deployment_generated_by_ddh.yml", help="Name of the output file"
    )
    parser.add_argument(
        "--head-rows",
        default=15,
        help="Number of lines to print to console after writing the deployment file",
    )
    args = parser.parse_args()

    generate_dab_deployment_file(
        environment=env, jobs_to_deploy=jobs, output_file=args.output_file, head_rows=args.head_rows
    )

if __name__ == "__main__":
    main()

>>> Generating DAB deployment file for 'DEV' ...
>>> Writing DAB deployment file to '~/databricks-deployment-helper/example_configuration/bundle_pipelines/dab_deployment_generated_by_ddh.yml' ...
>>> Output file successfully written.
>>>
>>> resources:
>>>   jobs:
>>>     _ad-hoc__bronze_complex:
>>>       job_clusters:
>>>       - job_cluster_key: cluster_complex_etl_bronze
>>>         new_cluster:
>>>           custom_tags:
>>>             ResourceClass: SingleNode
>>>             deployed_by: databricks_deployment_helper
>>>             entity: complex
>>>             entity_group: bronze_silver_gold_example
>>>             layer: bronze
>>>           data_security_mode: SINGLE_USER
>>>           driver_node_type_id: m5dn.xlarge
>>>           enable_elastic_disk: true
>>> ...
>>>
>>> To deploy this file please run
>>> databricks bundle deploy --target <your asset bundle target> [-p <your databricks-cli profile]
```

### DBX

```py
from databricks_deployment_helper.builders import *
from bundle_pipelines.jobs import example_job

envs = [
    Env.DEV,
    Env.PRD
]

jobs = [
    example_job
]

dbx_deployment = build_dbx_deployment_file(envs, jobs)

>>> {
>>>     "environments": {
>>>         "dev": {
>>>             "workflows": [
>>>                 {
>>>                     "name": "Example Jobs",
>>>                     "tags": "...",
>>>                     "...": "..."
>>>                 }
>>>             ]
>>>         },
>>>         "prd": {
>>>             "workflows": [
>>>                 {
>>>                     "name": "Example Jobs",
>>>                     "tags": "...",
>>>                     "...": "..."
>>>                 }
>>>             ]
>>>         }
>>>     }
>>> }
```

## Customization

Feel free to create your own models that inherit from the main models to facilitate the
creation of Job objects.

For example:

```python
from databricks_deployment_helper.models.task import Task
from dataclasses import field
from copy import deepcopy

default_libraries = [
    {"pypi": {"package": "mlflow==1.23.1"}}
]

class CustomTasks(Task):

    libraries = field(default_factory=lambda: deepcopy(default_libraries))
```

You can use CustomTasks instead of Tasks so that you don't have to specify the same
set of libraries in every Task definition.

### Examples

You can find examples in the folder `example_configuration`.

# Authors

- Emanuele Viglianisi (https://github.com/emavgl)
- David Hohensinn (https://github.com/Breaka84)
- Philip Buttinger (https://github.com/rt-phb)