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