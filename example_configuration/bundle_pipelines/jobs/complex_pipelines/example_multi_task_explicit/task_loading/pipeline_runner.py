import sys
from your_project.complex_pipelines import MultiTaskExplicit
from your_project.utils import read_config_file

environment = sys.argv[1]
databricks_config = read_config_file(environment=environment, config_file_path=sys.argv[2])


config = read_config_file(*sys.argv[1:3])
MultiTaskExplicit(config).load()
