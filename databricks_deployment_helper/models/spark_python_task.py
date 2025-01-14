import pathlib
from dataclasses import dataclass, field
from typing import List, Union, Dict

from databricks_deployment_helper.models.env import Env
from databricks_deployment_helper.models.environment_configuration import (
    EnvironmentConfiguration,
)
from databricks_deployment_helper.models.base_model import BaseModel


@dataclass
class SparkPythonTask(BaseModel):
    """
    SparkPythonTask contains the path to the python script to run :python_file and :databricks_config json.
    You can specify the parameters individually, or you can pass the parameter :path to
    set them using the naming convention: path + pipeline_runner.py and path + databricks_config.json.
    The list of parameter is set as: [target_environment] + :additional_parameters
    """

    path: Union[str, EnvironmentConfiguration] = None

    python_file: Union[str, EnvironmentConfiguration] = None
    databricks_config: Union[str, EnvironmentConfiguration] = None
    # Note: dbx deployment to azure uses lists while dabs deployment to AWS uses dictionaries
    custom_parameters: Union[dict, list, EnvironmentConfiguration] = field(
        default_factory=dict
    )

    def __post_init__(self):
        if self.path:
            if self.python_file is None:
                self.python_file = str(pathlib.Path(self.path, "pipeline_runner.py"))
            if self.databricks_config is None:
                self.databricks_config = str(
                    pathlib.Path(self.path, "databricks_config.json")
                )
        if not any([self.python_file, self.databricks_config]):
            raise ValueError(
                "Python file and databricks config must be set: "
                "set it explicitly or use the parameter 'path'"
            )
        super().__post_init__()

    @staticmethod
    def _ensure_file_path(target_value: Union[str, List[str]]) -> Union[str, List[str]]:
        """
        Ensures that paths start with `file://`

        Args:
            target_value: single string or list of strings

        Returns:
            single string or list of string with corrected paths
        """
        if isinstance(target_value, list):
            parameters = target_value
            corrected_parameters = []
            for parameter in parameters:
                corrected_parameter = parameter
                if "file://" not in parameter:
                    corrected_parameter = parameter.replace("file:/", "file://")
                corrected_parameters.append(corrected_parameter)
            return corrected_parameters
        else:
            parameter = target_value
            if "file://" not in target_value:
                return parameter.replace("file:/", "file://")
            return parameter

    def resolve(self, environment: Env = None) -> Dict:
        custom_parameters = self.custom_parameters.resolve(environment)
        if isinstance(custom_parameters, dict):
            # {'k1': 'v1', 'k2': 'v2'} -> ['k1', 'v1', 'k2', 'v2']
            custom_parameters = [item for pair in custom_parameters.items() for item in pair]
        resolved_python_file = self._ensure_file_path(
            self.python_file.resolve(environment)
        )
        resolved_parameters = self._ensure_file_path(
            [
                environment.value,
                self.databricks_config.resolve(environment),
            ]
            + custom_parameters
        )
        return {
            "python_file": resolved_python_file,
            "parameters": resolved_parameters,
        }
