from dataclasses import dataclass, asdict
from typing import Any
from abc import ABC, abstractmethod

from databricks_deployment_helper.models.env import Env
from databricks_deployment_helper.models.environment_configuration import (
    EnvironmentConfiguration,
)


@dataclass
class BaseModel(ABC):
    """
    BaseModel is an abstract class all the models should inherit from.
    It forces the models to implement the method resolve and provides
    an implementations for the method __post_init__ to convert each field
    to EnvironmentConfiguration instances.
    """

    @abstractmethod
    def resolve(self, environment: Env = None) -> Any:
        """
        Resolve the value for the specified environment.

        Args:
            environment: target environment

        Returns:
            resolved value (most of the time dictionary, or basic type)
        """
        pass

    def __post_init__(self):
        for field_name in asdict(self).keys():
            field_value = getattr(self, field_name)
            if not isinstance(field_value, EnvironmentConfiguration):
                setattr(self, field_name, EnvironmentConfiguration(default=field_value))
