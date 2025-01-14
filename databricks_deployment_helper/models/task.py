from dataclasses import dataclass, field
from typing import List, Union, Dict

from databricks_deployment_helper.models.clusters import Cluster
from databricks_deployment_helper.models.env import Env
from databricks_deployment_helper.models.spark_python_task import SparkPythonTask
from databricks_deployment_helper.models.environment_configuration import (
    EnvironmentConfiguration,
)
from databricks_deployment_helper.models.base_model import BaseModel
from databricks_deployment_helper.models.email_notification import EmailNotification


@dataclass
class Task(BaseModel):
    # mandatory
    spark_python_task: SparkPythonTask

    # default
    task_key: Union[str, EnvironmentConfiguration] = "job_task"
    description: Union[str, EnvironmentConfiguration] = None
    depends_on: Union[List[Dict], EnvironmentConfiguration] = field(
        default_factory=list
    )
    job_cluster_key: Union[str, EnvironmentConfiguration] = "job_cluster"
    libraries: Union[List[Dict], EnvironmentConfiguration] = field(default_factory=list)
    additional_libraries: Union[List[Dict], EnvironmentConfiguration] = field(default_factory=list)
    max_retries: Union[int, EnvironmentConfiguration] = 0
    new_cluster: Union[Cluster, EnvironmentConfiguration] = None
    email_notifications: Union[EmailNotification, EnvironmentConfiguration] = None

    def resolve(self, environment: Env = None) -> Dict:
        if duplicate_libraries := [
            item for item in self.additional_libraries.resolve(environment)
            if item in self.libraries.resolve(environment)
        ]:
            raise RuntimeError(
                f"Following libraries have been specified multiple times: {duplicate_libraries} "
                f"for the task: {self.spark_python_task.resolve(environment)['python_file']}"
            )

        return_dict = {
            "task_key": self.task_key.resolve(environment),
            "description": self.description.resolve(environment),
            "libraries": self.libraries.resolve(environment) + self.additional_libraries.resolve(environment),
            "max_retries": self.max_retries.resolve(environment),
            "depends_on": self.depends_on.resolve(environment),
            "spark_python_task": self.spark_python_task.resolve(environment),
        }
        if (new_cluster := self.new_cluster.resolve(environment)) is not None:
            return_dict["new_cluster"] = new_cluster
        else:
            return_dict["job_cluster_key"] = self.job_cluster_key.resolve(environment)

        if (
            email_notifications := self.email_notifications.resolve(environment)
        ) is not None:
            return_dict["email_notifications"] = email_notifications
        return return_dict
