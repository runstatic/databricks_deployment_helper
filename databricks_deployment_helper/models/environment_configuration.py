from dataclasses import dataclass, field
from typing import Dict, Any
from enum import Enum

from databricks_deployment_helper.models.env import Env


@dataclass
class EnvironmentConfiguration:
    """
    EnvironmentConfiguration is a class that represents an environment dependent configuration.
    It contains a map, called :environments_map that maps environment and the field configuration for that environment.
    It has also a field :default, that is used if the target environment is not present in the :environments_map.

    We want to give the possibility to the user to define an environment configuration for every field.
    For simplification, each field is converted to EnvironmentConfiguration implicitly
    by the BaseModel.__post_init__ function.
    """

    environments_map: Dict[Env, Any] = field(default_factory=dict)
    default: Any = None

    def resolve(self, environment: Env) -> Any:
        """
        Gets the configuration for the target environment :environment

        Args:
            environment: target environment

        Returns:
            field configuration for the target environment
        """
        env_specific_value: Any = self.environments_map.get(environment, self.default)

        def _resolve(obj: Any, env: Env):
            """
            Calls the resolve method of obj if available.
            If obj is of type Enum then returns the value of the enum.
            If obj does not implement the resolve method and is not of type Enum (basic types) then it returns obj
            itself.

            Args:
                obj: object on which to call resolve
                env: target environment

            Returns:
                resolved object
            """
            if hasattr(obj, "resolve"):
                return obj.resolve(env)
            if isinstance(obj, Enum):
                return obj.value
            return obj

        if isinstance(env_specific_value, list):
            return [_resolve(val, environment) for val in env_specific_value]
        else:
            return _resolve(env_specific_value, environment)
