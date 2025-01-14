from dataclasses import dataclass
from pathlib import Path
from typing import Union, Dict

from databricks_deployment_helper.models import *


def working_dir_of_current_file() -> str:
    return f"file://{Path(__file__).parent}"


default_data_service_schedule = CronSchedule(
    "0 0 8 ? * *", pause_status=PauseStatus.UNPAUSED
)


spark_configs_data_etl = EnvironmentConfiguration(
    {
        Env.DEV: {
            "spark.hadoop.fs.azure.account.auth.type.<dev-storage>.dfs.core.windows.net": "OAuth",
            "spark.hadoop.fs.azure.account.oauth2.client.endpoint.<dev-storage>.dfs.core.windows.net": "https://login.microsoftonline.com/<dev-token>/oauth2/token",
            "spark.hadoop.fs.azure.account.oauth.provider.type.<dev-storage>.dfs.core.windows.net": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
            "spark.hadoop.fs.azure.account.oauth2.client.id.<dev-storage>.dfs.core.windows.net": "<dev-client-id>",
            "spark.hadoop.fs.azure.account.oauth2.client.secret.<dev-storage>.dfs.core.windows.net": "{{secrets/dev/oath-secret}}",
        },
        Env.STG: {
            "spark.hadoop.fs.azure.account.auth.type.<stg-storage>.dfs.core.windows.net": "OAuth",
            "spark.hadoop.fs.azure.account.oauth2.client.endpoint.<stg-storage>.dfs.core.windows.net": "https://login.microsoftonline.com/<stg-token>/oauth2/token",
            "spark.hadoop.fs.azure.account.oauth.provider.type.<stg-storage>.dfs.core.windows.net": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
            "spark.hadoop.fs.azure.account.oauth2.client.id.<stg-storage>.dfs.core.windows.net": "<stg-client-id>",
            "spark.hadoop.fs.azure.account.oauth2.client.secret.<stg-storage>.dfs.core.windows.net": "{{secrets/stg/oath-secret}}",
        },
        Env.PRE: {
            "spark.hadoop.fs.azure.account.auth.type.<pre-storage>.dfs.core.windows.net": "OAuth",
            "spark.hadoop.fs.azure.account.oauth2.client.endpoint.<pre-storage>.dfs.core.windows.net": "https://login.microsoftonline.com/<pre-token>/oauth2/token",
            "spark.hadoop.fs.azure.account.oauth.provider.type.<pre-storage>.dfs.core.windows.net": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
            "spark.hadoop.fs.azure.account.oauth2.client.id.<pre-storage>.dfs.core.windows.net": "<pre-client-id>",
            "spark.hadoop.fs.azure.account.oauth2.client.secret.<pre-storage>.dfs.core.windows.net": "{{secrets/pre/oath-secret}}",
        },
        Env.PRD: {
            "spark.hadoop.fs.azure.account.auth.type.<prd-storage>.dfs.core.windows.net": "OAuth",
            "spark.hadoop.fs.azure.account.oauth2.client.endpoint.<prd-storage>.dfs.core.windows.net": "https://login.microsoftonline.com/<prd-token>/oauth2/token",
            "spark.hadoop.fs.azure.account.oauth.provider.type.<prd-storage>.dfs.core.windows.net": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
            "spark.hadoop.fs.azure.account.oauth2.client.id.<prd-storage>.dfs.core.windows.net": "<prd-client-id>",
            "spark.hadoop.fs.azure.account.oauth2.client.secret.<prd-storage>.dfs.core.windows.net": "{{secrets/prd/oath-secret}}",
        },
    }
)

cluster_libraries_runtime = [
    {"pypi": {"package": "mlflow == 1.23.1"}},
    {"pypi": {"package": "python-dotenv == 0.10.3"}},
    {"pypi": {"package": "scikit-learn == 0.22"}},
    {"pypi": {"package": "jsonschema == 4.6.0"}},
    {"pypi": {"package": "nose == 1.3.7"}},
    {"pypi": {"package": "python-json-config == 1.2.3"}},
    {"pypi": {"package": "spooq == 3.3.9"}},
    {"pypi": {"package": "glom == 22.1.0"}},
    {"pypi": {"package": "azure-core == 1.24.1"}},
    {"pypi": {"package": "azure-identity == 1.10.0"}},
    {"pypi": {"package": "azure-storage-blob == 12.12.0"}},
    {"pypi": {"package": "azure-storage-file-datalake == 12.7.0"}},
    {"pypi": {"package": "json-api-doc == 0.15.0"}},
    {"pypi": {"package": "pika == 1.2.1"}},
    {"pypi": {"package": "tenacity == 8.0.1"}},
    {"pypi": {"package": "gspread == 5.4.0"}},
    {"pypi": {"package": "databricks-api == 0.8.0"}},
]

default_email_notifications = EnvironmentConfiguration(
    {
        Env.STG: EmailNotification(on_failure=["stg@example.com"]),
        Env.PRE: EmailNotification(on_failure=["pre@example.com"]),
        Env.PRD: EmailNotification(on_failure=["prd@example.com"]),
    }
)


@dataclass()
class BaseCluster(Cluster):
    node_type_id: Union[
        ClusterNodeType, EnvironmentConfiguration
    ] = AzureClusterNodeType.Standard_F4
    spark_version: Union[str, EnvironmentConfiguration] = "12.1.x-scala2.12"
    number_of_workers: Union[int, dict, EnvironmentConfiguration] = 0
    spark_conf: Union[Dict, EnvironmentConfiguration] = spark_configs_data_etl
