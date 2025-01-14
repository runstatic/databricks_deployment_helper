from dataclasses import field, dataclass
from typing import Dict, Union

from databricks_deployment_helper.models import Cluster, ClusterNodeType, EnvironmentConfiguration, AWSClusterNodeType


SPARK_VERSION = "14.3.x-scala2.12"


@dataclass
class BaseCluster(Cluster):
    node_type_id: Union[ClusterNodeType, EnvironmentConfiguration] = field(
        default=AWSClusterNodeType.GeneralPurpose.m5dn_xlarge
    )
    spark_version: Union[str, EnvironmentConfiguration] = SPARK_VERSION
    number_of_workers: Union[int, EnvironmentConfiguration] = 0
    policy_id: str = "${var.job_policy_id}"
    data_security_mode: str = "SINGLE_USER"
    base_tags: Dict = field(default_factory=lambda: {"deployed_by": "databricks_deployment_helper"})
