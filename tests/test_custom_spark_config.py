import pytest

from databricks_deployment_helper.models import Cluster, EnvironmentConfiguration, AzureClusterNodeType, Env


CUSTOM_SPARK_SETTING_NAME = "spark.sql.shuffle.partitions"


@pytest.fixture()
def cluster() -> Cluster:
    base_spark_config = EnvironmentConfiguration(
        {
            Env.DEV: {
                "spark.hadoop.fs.azure.account.auth.type.<datalake_dev>.dfs.core.windows.net": "OAuth",
                CUSTOM_SPARK_SETTING_NAME: 1024

            },
            Env.STG: {
                "spark.hadoop.fs.azure.account.auth.type.<datalake_stg>.dfs.core.windows.net": "OAuth",
            },
            Env.PRD: {
                "spark.hadoop.fs.azure.account.auth.type.<datalake_prd>.dfs.core.windows.net": "OAuth",
            }
        }
    )
    custom_spark_config = EnvironmentConfiguration({
        Env.DEV: {CUSTOM_SPARK_SETTING_NAME: 2048},
        Env.PRD: {CUSTOM_SPARK_SETTING_NAME: 2000}
    }, default=None)

    return Cluster(
        node_type_id=AzureClusterNodeType.Standard_D4_v2,
        number_of_workers=2,
        spark_conf=base_spark_config,
        custom_spark_conf=custom_spark_config
    )


@pytest.fixture()
def resolved_cluster_dev(cluster: Cluster) -> dict:
    return cluster.resolve(environment=Env.DEV)


@pytest.fixture()
def resolved_cluster_prd(cluster: Cluster) -> dict:
    return cluster.resolve(environment=Env.PRD)


@pytest.fixture()
def resolved_cluster_stg(cluster: Cluster) -> dict:
    return cluster.resolve(environment=Env.STG)


def test_custom_spark_setting_is_updated_correctly(resolved_cluster_dev: dict):
    assert resolved_cluster_dev["spark_conf"] == {
        "spark.hadoop.fs.azure.account.auth.type.<datalake_dev>.dfs.core.windows.net": "OAuth",
        CUSTOM_SPARK_SETTING_NAME: 2048
    }


def test_custom_spark_setting_is_added_correctly(resolved_cluster_prd: dict):
    assert resolved_cluster_prd["spark_conf"] == {
        "spark.hadoop.fs.azure.account.auth.type.<datalake_prd>.dfs.core.windows.net": "OAuth",
        CUSTOM_SPARK_SETTING_NAME: 2000
    }


def test_custom_spark_setting_is_not_added_when_not_defined(resolved_cluster_stg: dict):
    assert resolved_cluster_stg["spark_conf"] == {
         "spark.hadoop.fs.azure.account.auth.type.<datalake_stg>.dfs.core.windows.net": "OAuth",
    }