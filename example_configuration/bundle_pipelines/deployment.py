import argparse
import json

from databricks_deployment_helper.models import Env
from databricks_deployment_helper.builders import generate_dab_deployment_file, build_dbx_deployment_file

from jobs.bronze_silver_gold import (
    example_pipeline_non_standard,
    example_pipeline_simple
)
from jobs.complex_pipelines.example_multi_task_explicit import multi_task_explicit_job

envs = [Env.DEV, Env.STG, Env.PRE, Env.PRD]

jobs = [
    *example_pipeline_simple.jobs,
    *example_pipeline_non_standard.jobs,
    multi_task_explicit_job
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-e",
        "--env",
        default="dev",
        type=lambda env: Env[env.upper()],
        help="For which environment the deployment file should be generated. Defaults to 'dev'.",
    )
    parser.add_argument(
        "-b",
        "--backend",
        default="dab",
        type=lambda backend: backend.lower(),
        help="For which deployment backend should the jobs be prepared? 'DAB' or 'DBX' are currently supported. Defaults to 'DAB'.",
    )
    parser.add_argument(
        "-o", "--output-file", default="dab_deployment_generated_by_ddh.yml", help="Name of the output file. Defaults to 'dab_deployment_generated_by_ddh.yml'."
    )
    parser.add_argument(
        "--head-rows",
        default=15,
        help="Number of lines to print to console after writing the deployment file. Defaults to 15.",
    )
    args = parser.parse_args()

    if args.backend == "dab":
        generate_dab_deployment_file(
            environment=args.env, jobs_to_deploy=jobs, output_file=args.output_file, head_rows=args.head_rows
        )
    elif args.backend == "dbx":
        dbx_deployment = build_dbx_deployment_file(envs, jobs)

        deployment_str = json.dumps(dbx_deployment, indent=2)
        file_name = "deployment.json"

        print("Writing to file:", file_name)
        with open(file_name, "w") as file:
            file.write(deployment_str)
    else:
        raise RuntimeError(f"Type of deployment backend not supported: '{args.backend}'! Only 'DAB' and 'DBX' are supported.")


if __name__ == "__main__":
    main()
