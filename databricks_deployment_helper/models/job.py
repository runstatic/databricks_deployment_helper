from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Union, Dict

from databricks_deployment_helper.models.base_model import BaseModel
from databricks_deployment_helper.models.clusters import JobCluster
from databricks_deployment_helper.models.env import Env
from databricks_deployment_helper.models.email_notification import EmailNotification
from databricks_deployment_helper.models.environment_configuration import (
    EnvironmentConfiguration,
)
from databricks_deployment_helper.models.schedule import CronSchedule
from databricks_deployment_helper.models.task import Task


@dataclass
class Job(BaseModel):
    name: Union[str, EnvironmentConfiguration]
    tags: Union[Dict, EnvironmentConfiguration]
    tasks: Union[List[Task], EnvironmentConfiguration]

    email_notifications: Union[EmailNotification, EnvironmentConfiguration] = None
    job_clusters: Union[List[JobCluster], EnvironmentConfiguration] = field(
        default_factory=list
    )
    schedule: Union[CronSchedule, EnvironmentConfiguration] = None
    to_deploy: Union[bool, EnvironmentConfiguration] = field(default=True)

    def __post_init__(self):
        self.tags = deepcopy(self.tags)
        super().__post_init__()

    def resolve(self, environment: Env = None) -> Dict:
        job_clusters: List[Dict] = deepcopy(self.job_clusters.resolve(environment))
        tags = self.tags.resolve(environment)
        for cluster in job_clusters:
            for tag_key, tag_value in tags.items():
                cluster["new_cluster"]["custom_tags"].setdefault(tag_key, tag_value)
        return_dict = {
            "name": self.name.resolve(environment),
            "tags": tags,
            "tasks": self.tasks.resolve(environment),
            "job_clusters": job_clusters,
        }
        if (schedule := self.schedule.resolve(environment)) is not None:
            return_dict["schedule"] = schedule
        if (
            email_notifications := self.email_notifications.resolve(environment)
        ) is not None:
            return_dict["email_notifications"] = email_notifications
        return return_dict
