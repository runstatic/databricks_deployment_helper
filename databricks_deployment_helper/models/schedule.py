from dataclasses import dataclass
from enum import Enum
from typing import Union, Dict

from databricks_deployment_helper.models.env import Env
from databricks_deployment_helper.models.environment_configuration import (
    EnvironmentConfiguration,
)
from databricks_deployment_helper.models.base_model import BaseModel


class PauseStatus(Enum):
    PAUSED = "PAUSED"
    UNPAUSED = "UNPAUSED"

    def resolve(self, environment: Env = None):
        return self.value


@dataclass
class CronSchedule(BaseModel):
    # mandatory
    quartz_cron_expression: Union[str, EnvironmentConfiguration]

    # default
    timezone_id: Union[str, EnvironmentConfiguration] = "Europe/Vienna"
    pause_status: Union[PauseStatus, EnvironmentConfiguration] = PauseStatus.PAUSED

    def resolve(self, environment: Env = None) -> Dict:
        return {
            "timezone_id": self.timezone_id.resolve(environment),
            "quartz_cron_expression": self.quartz_cron_expression.resolve(environment),
            "pause_status": self.pause_status.resolve(environment),
        }
