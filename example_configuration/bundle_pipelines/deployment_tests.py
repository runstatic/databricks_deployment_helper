import argparse

from databricks_deployment_helper.models import Env
from databricks_deployment_helper.builders import generate_dab_deployment_file

from jobs.databricks_tests.deployment import databricks_tests

env = Env.DEV

jobs = [databricks_tests]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", "--output-file", default="dab_deployment_generated_by_ddh.yml", help="Name of the output file"
    )
    parser.add_argument(
        "--head-rows",
        default=15,
        help="Number of lines to print to console after writing the deployment file",
    )
    args = parser.parse_args()

    generate_dab_deployment_file(
        environment=env, jobs_to_deploy=jobs, output_file=args.output_file, head_rows=args.head_rows
    )


if __name__ == "__main__":
    main()
