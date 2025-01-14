import sys

from your_project.gold import GoldExamplePipeline
from your_project.utils import read_config_file

config = read_config_file(environment=sys.argv[1], config_file_path=sys.argv[2])
GoldExamplePipeline(config=config).run()
