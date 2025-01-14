from typing import Union
from dataclasses import dataclass

from databricks_deployment_helper.models.job import Job
from databricks_deployment_helper.models.email_notification import EmailNotification
from databricks_deployment_helper.models.environment_configuration import EnvironmentConfiguration

from ddh_config.email_notifications import default_email_notifications


@dataclass
class CustomizedJob(Job):
    email_notifications: Union[EmailNotification, EnvironmentConfiguration] = default_email_notifications
