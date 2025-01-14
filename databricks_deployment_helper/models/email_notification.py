from dataclasses import dataclass, field
from typing import Union, List, Dict

from databricks_deployment_helper.models.env import Env
from databricks_deployment_helper.models.environment_configuration import (
    EnvironmentConfiguration,
)
from databricks_deployment_helper.models.base_model import BaseModel


@dataclass
class EmailNotification(BaseModel):
    # default
    on_start: Union[List[str], EnvironmentConfiguration] = field(default_factory=list)
    on_success: Union[List[str], EnvironmentConfiguration] = field(default_factory=list)
    on_failure: Union[List[str], EnvironmentConfiguration] = field(default_factory=list)
    no_alert_for_skipped_runs: Union[bool, EnvironmentConfiguration] = field(
        default=False
    )

    def resolve(self, environment: Env = None) -> Dict:
        return {
            "on_start": self.on_start.resolve(environment),
            "on_success": self.on_success.resolve(environment),
            "on_failure": self.on_failure.resolve(environment),
            "no_alert_for_skipped_runs": self.no_alert_for_skipped_runs.resolve(
                environment
            ),
        }
