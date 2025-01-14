from ddh_config.libraries import Lib
from ddh_config.utils import working_dir_of_current_file
from ddh_config.bronze_silver_gold_utils import (
    combine_single_task_jobs,
    generate_single_task_job,
)

from databricks_deployment_helper.models import AWSClusterNodeType
from databricks_deployment_helper.models import EnvironmentConfiguration, Env

# --------------------------------------------- NON-STANDARD CONFIG ---------------------------------------------------
custom_config_silver = {
    "cluster": {
        "node_type_id": EnvironmentConfiguration(
            environments_map={Env.STG: AWSClusterNodeType.ComputeOptimized.c5a_xlarge},
            default=AWSClusterNodeType.ComputeOptimized.c5a_4xlarge,
        ),
    },
    "task": {"additional_libraries": [Lib.some_other_wheel]},
}

custom_config_gold_1 = {
    "job_name": "Gold: Non standard Example 1",
    "cluster": custom_config_silver["cluster"],
    "task": {
        "task_key": "gold_1",
        "task_folder": "task_gold_1",
    },
}

custom_config_gold_2 = {
    "job_name": "Gold: Non standard Example 2",
    "cluster": custom_config_silver["cluster"],
    "task": {
        "task_key": "gold_2",
        "task_folder": "task_gold_2",
    },
}


# ----------------------------------------------- GENERATE JOBS --------------------------------------------------------
shared_parameters = dict(entity_group="bronze_silver_gold_example", entity_name="complex", working_dir=working_dir_of_current_file())

bronze_job = generate_single_task_job(layer="bronze", **shared_parameters)
silver_job = generate_single_task_job(layer="silver", custom_config=custom_config_silver, **shared_parameters)
gold_job_1 = generate_single_task_job(layer="gold", custom_config=custom_config_gold_1, **shared_parameters)
gold_job_2 = generate_single_task_job(layer="gold", custom_config=custom_config_gold_2, **shared_parameters)

bronze_silver_gold_job = combine_single_task_jobs(
    layer="bronze_silver_gold",
    entity_group=shared_parameters["entity_group"],
    entity_name=shared_parameters["entity_name"],
    jobs=[bronze_job, silver_job, gold_job_1, gold_job_2],
    dependency_mapping={
        gold_job_1.name.default: [silver_job.name.default],
        gold_job_2.name.default: [silver_job.name.default],
        silver_job.name.default: [bronze_job.name.default],
        bronze_job.name.default: None,
    },
)

jobs = [bronze_job, silver_job, gold_job_1, gold_job_2, bronze_silver_gold_job]
