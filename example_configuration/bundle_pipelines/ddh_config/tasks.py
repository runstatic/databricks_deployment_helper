from dataclasses import dataclass

from databricks_deployment_helper.models.task import Task
from ddh_config.libraries import LIBRARIES_BRONZE, LIBRARIES_SILVER_GOLD, LIBRARIES_BASE


@dataclass
class RetryingTask(Task):
    def __post_init__(self):
        self.libraries = self.libraries or LIBRARIES_BASE
        self.max_retries = 1
        super().__post_init__()


@dataclass
class BronzeTask(RetryingTask):
    def __post_init__(self):
        self.libraries = LIBRARIES_BRONZE
        super().__post_init__()


@dataclass
class SilverGoldTask(RetryingTask):
    def __post_init__(self):
        self.libraries = LIBRARIES_SILVER_GOLD
        super().__post_init__()
