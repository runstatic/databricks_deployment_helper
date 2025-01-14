import sys
from your_project.complex_pipelines import MultiTaskExplicit
from your_project.utils import read_config_file

environment = sys.argv[1]
databricks_config = read_config_file(environment=environment, config_file_path=sys.argv[2])  # databricks_config.json
extra_config = read_config_file(environment=environment, config_file_path=sys.argv[3])  # extra_file_needed_for_processing.json

MultiTaskExplicit(databricks_config, extra_config).process()
