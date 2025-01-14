import sys

from your_project.silver import SilverExamplePipeline
from your_project.utils import read_config_file

config = read_config_file(environment=sys.argv[1], config_file_path=sys.argv[2])
SilverExamplePipeline(config=config).run()
