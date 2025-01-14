import sys
from your_project.bronze import BronzeExamplePipeline
from your_project.utils import read_config_file

environment = sys.argv[1]
databricks_config = read_config_file(environment=environment, config_file_path=sys.argv[2])

BronzeExamplePipeline(databricks_config=databricks_config).run()
