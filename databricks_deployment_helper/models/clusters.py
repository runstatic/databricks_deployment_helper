from dataclasses import dataclass, field
from typing import Union, Dict
from copy import deepcopy

from databricks_deployment_helper.models.cluster_node_types import ClusterNodeType
from databricks_deployment_helper.models.env import Env
from databricks_deployment_helper.models.environment_configuration import (
    EnvironmentConfiguration,
)
from databricks_deployment_helper.models.base_model import BaseModel


@dataclass
class Cluster(BaseModel):
    """
    Cluster requires a node_type_id.
    In addition to a selection of fields required to create a new job cluster (check databricks docs Jobs 2.1)
    it contains:
        - base_tags: a set of tags to be merged into custom_tags with the intention of defining the tags in subclasses.
    """

    node_type_id: Union[ClusterNodeType, EnvironmentConfiguration]

    spark_version: Union[str, EnvironmentConfiguration] = "11.3.x-scala2.12"
    runtime_engine: Union[str, EnvironmentConfiguration] = "STANDARD"
    driver_node_type_id: Union[ClusterNodeType, EnvironmentConfiguration] = None
    number_of_workers: Union[int, dict, EnvironmentConfiguration] = 4
    enable_elastic_disk: Union[str, EnvironmentConfiguration] = True
    data_security_mode: Union[str, EnvironmentConfiguration] = None
    policy_id: Union[str, EnvironmentConfiguration] = None

    base_tags: Dict = field(
        init=False, default_factory=dict
    )  # tags to be defined in subclasses
    spark_conf: Union[Dict, EnvironmentConfiguration] = field(default_factory=dict)
    custom_spark_conf: Union[Dict, EnvironmentConfiguration] = field(default_factory=dict)
    custom_tags: Union[Dict, EnvironmentConfiguration] = field(default_factory=dict)

    def __post_init__(self):
        self.spark_conf = deepcopy(self.spark_conf)
        self.custom_spark_conf = deepcopy(self.custom_spark_conf)
        self.custom_tags = deepcopy(self.custom_tags)
        self.base_tags = deepcopy(self.base_tags)
        self.custom_tags.update(self.base_tags)
        if self.driver_node_type_id is None:
            self.driver_node_type_id = self.node_type_id
        super().__post_init__()

    def resolve(self, environment: Env = None) -> Dict:
        number_of_workers: Union[int, dict] = self.number_of_workers.resolve(environment)
        custom_spark_conf: Dict = self.custom_spark_conf.resolve(environment)
        spark_conf: Dict = deepcopy(self.spark_conf.resolve(environment))
        custom_tags: Dict = deepcopy(self.custom_tags.resolve(environment))
        if custom_spark_conf:
            spark_conf.update(custom_spark_conf)

        if isinstance(number_of_workers, int):
            if number_of_workers == 0:
                single_node_spark_conf = {
                    "spark.master": "local[*]",
                    "spark.databricks.cluster.profile": "singleNode",
                }
                spark_conf.update(single_node_spark_conf)
                custom_tags.update({"ResourceClass": "SingleNode"})
            worker_config = {"num_workers": number_of_workers}
        elif isinstance(number_of_workers, dict):
            worker_config = {"autoscale": number_of_workers}
        else:
            raise ValueError("num_workers must be of type dict or int!")

        data_security_mode = self.data_security_mode.resolve(environment)
        policy_id = self.policy_id.resolve(environment)
        return dict(
            spark_version=self.spark_version.resolve(environment),
            custom_tags=custom_tags,
            runtime_engine=self.runtime_engine.resolve(environment),
            node_type_id=self.node_type_id.resolve(environment),
            driver_node_type_id=self.driver_node_type_id.resolve(environment),
            spark_conf=spark_conf,
            enable_elastic_disk=self.enable_elastic_disk.resolve(environment),
            **worker_config,
            **dict(data_security_mode=data_security_mode) if data_security_mode else {},
            **dict(policy_id=policy_id) if policy_id else {},
        )


@dataclass
class JobCluster(BaseModel):
    job_cluster_key: Union[str, EnvironmentConfiguration]
    new_cluster: Union[Cluster, EnvironmentConfiguration]

    def resolve(self, environment: Env = None):
        return {
            "job_cluster_key": self.job_cluster_key.resolve(environment),
            "new_cluster": self.new_cluster.resolve(environment),
        }