from typing import Any, List

import pytest
from pytest import FixtureRequest
import glom
from glom import T, flatten
from glom.core import TType

from ddh_config.jobs import CustomizedJob
from ddh_config.libraries import Lib
from ddh_config.cluster import SPARK_VERSION
from ddh_config.bronze_silver_gold_utils import (
    combine_single_task_jobs,
    generate_bronze_silver_gold_jobs,
    generate_single_task_job,
)
from ddh_config.utils import SHARED_CONFIG_DIR
from databricks_deployment_helper.models.env import Env
from databricks_deployment_helper.models.environment_configuration import EnvironmentConfiguration
from databricks_deployment_helper.models import AWSClusterNodeType


@pytest.fixture(scope="module")
def working_dir_of_current_file() -> str:
    return "file://path/to/working/dir"


@pytest.fixture(scope="module")
def bronze_silver_gold_jobs(working_dir_of_current_file: str) -> List[CustomizedJob]:
    return generate_bronze_silver_gold_jobs(
        entity_group="test_entity_group",
        entity_name="test_entity",
        working_dir=working_dir_of_current_file,
    )


@pytest.fixture(scope="module")
def bronze_adhoc_job(bronze_silver_gold_jobs: List[CustomizedJob]) -> dict:
    return bronze_silver_gold_jobs[0].resolve(Env.PRD)


@pytest.fixture(scope="module")
def silver_adhoc_job(bronze_silver_gold_jobs: List[CustomizedJob]) -> dict:
    return bronze_silver_gold_jobs[1].resolve(Env.PRD)


@pytest.fixture(scope="module")
def gold_adhoc_job(bronze_silver_gold_jobs: List[CustomizedJob]) -> dict:
    return bronze_silver_gold_jobs[2].resolve(Env.PRD)


@pytest.fixture(scope="module")
def bronze_silver_gold_job(bronze_silver_gold_jobs: List[CustomizedJob]) -> dict:
    return bronze_silver_gold_jobs[3].resolve(Env.PRD)


# Shortcuts for accessing nested attributes with glom (`T` marks the root of the dict)
JOB_TAGS = T["tags"]
JOB_SCHEDULE = T["schedule"]
TASKS = T["tasks"]
TASK = TASKS[0]
SPARK_PYTHON_TASK = TASK["spark_python_task"]
JOB_CLUSTERS = T["job_clusters"]
JOB_CLUSTER = JOB_CLUSTERS[0]
NEW_CLUSTER = JOB_CLUSTER["new_cluster"]
CLUSTER_TAGS = NEW_CLUSTER["custom_tags"]
SPARK_CONF = NEW_CLUSTER["spark_conf"]


@pytest.mark.parametrize(
    # fmt: off
    argnames=[
        "job_fixture_name",   "layer",   "permission_group"
    ],
    argvalues=[
        ("bronze_adhoc_job",  "bronze",  "etl"),
        ("silver_adhoc_job",  "silver",  "etl"),
        ("gold_adhoc_job",    "gold",    "etl"),
    ]
    # fmt: on
)
class TestDefaultAdHocJob:
    def test_job_name(self, job_fixture_name: str, layer: str, permission_group: str, request: FixtureRequest):
        job_to_test = request.getfixturevalue(job_fixture_name)
        assert glom.glom(job_to_test, "name") == f"[Ad-Hoc] {layer.capitalize()}: Test Entity"

    def test_schedule(self, job_fixture_name: str, layer: str, permission_group: str, request: FixtureRequest):
        job_to_test = request.getfixturevalue(job_fixture_name)
        assert "schedule" not in job_to_test

    @pytest.mark.parametrize(
        ["key", "expected_value"],
        # fmt: off
        [
            (TASK["task_key"],                   "{layer}_test_entity"),
            (SPARK_PYTHON_TASK["python_file"],   "{cwd}/task_{layer}/pipeline_runner.py"),
            (SPARK_PYTHON_TASK["parameters"][1], "{cwd}/task_{layer}/databricks_config.json"),
            (SPARK_PYTHON_TASK["parameters"][0], "PRD"),
        ]
        # fmt: on
    )
    def test_task(
        self,
        key: TType,
        expected_value: str,
        job_fixture_name: str,
        layer: str,
        permission_group: str,
        request: FixtureRequest,
        working_dir_of_current_file: str,
    ):
        job_to_test = request.getfixturevalue(job_fixture_name)
        assert glom.glom(job_to_test, key) == expected_value.format(cwd=working_dir_of_current_file, layer=layer)

    @pytest.mark.parametrize("expected_library", ["glom", "spooq"])
    def test_libraries(
        self, expected_library: str, job_fixture_name: str, layer: str, permission_group: str, request: FixtureRequest
    ):
        job_to_test = request.getfixturevalue(job_fixture_name)
        defined_libraries = [lib.split(" == ")[0] for lib in glom.glom(job_to_test, "tasks.0.libraries.*.pypi.package")]
        assert expected_library in defined_libraries

    @pytest.mark.parametrize(
        ["key", "expected_tag"],
        # fmt: off
        [
            (JOB_TAGS["entity_group"],      "test_entity_group"),
            (JOB_TAGS["entity"],            "test_entity"),
            (JOB_TAGS["layer"],             "{layer}"),
            (CLUSTER_TAGS["layer"],         "{layer}"),
            (CLUSTER_TAGS["entity_group"],  "test_entity_group"),
            (CLUSTER_TAGS["entity"],        "test_entity"),
            (CLUSTER_TAGS["ResourceClass"], "SingleNode"),
        ]
        # fmt: on
    )
    def test_tags(
        self,
        key: TType,
        expected_tag: Any,
        job_fixture_name: str,
        layer: str,
        permission_group: str,
        request: FixtureRequest,
    ):
        job_to_test = request.getfixturevalue(job_fixture_name)
        assert glom.glom(job_to_test, key) == expected_tag.format(layer=layer)

    @pytest.mark.parametrize(
        ["key", "expected_value"],
        # fmt: off
        [
            (JOB_CLUSTER["job_cluster_key"],     "cluster_test_entity_{permission_group}_{layer}"),
            (NEW_CLUSTER["spark_version"],       SPARK_VERSION),
            (NEW_CLUSTER["runtime_engine"],      "STANDARD"),
            (NEW_CLUSTER["node_type_id"],        "m5dn.xlarge"),
            (NEW_CLUSTER["driver_node_type_id"], "m5dn.xlarge"),
        ]
        # fmt: on
    )
    def test_cluster(
        self,
        key: TType,
        expected_value: Any,
        job_fixture_name: str,
        layer: str,
        permission_group: str,
        request: FixtureRequest,
    ):
        job_to_test = request.getfixturevalue(job_fixture_name)
        assert glom.glom(job_to_test, key) == expected_value.format(layer=layer, permission_group=permission_group)

    @pytest.mark.parametrize(
        "expected_key",
        # fmt: off
        [
            "spark.master",
            "spark.databricks.cluster.profile",
        ]
        # fmt: on
    )
    def test_spark_configs(
        self, expected_key: str, job_fixture_name: str, layer: str, permission_group: str, request: FixtureRequest
    ):
        job_to_test = request.getfixturevalue(job_fixture_name)
        assert expected_key in glom.glom(job_to_test, SPARK_CONF)

    @pytest.mark.parametrize(
        argnames=["key", "expected_count"],
        argvalues=[
            (TASKS.__("len__")(), 1),
            (TASK["max_retries"], 1),
            (TASK["depends_on"].__("len__")(), 0),
            (JOB_CLUSTERS.__("len__")(), 1),
            (NEW_CLUSTER["num_workers"], 0),
            (NEW_CLUSTER["spark_conf"].__("len__")(), 2),
        ],
    )
    def test_counts(
        self,
        key: TType,
        expected_count: int,
        job_fixture_name: str,
        layer: str,
        permission_group: str,
        request: FixtureRequest,
    ):
        job_to_test = request.getfixturevalue(job_fixture_name)
        assert glom.glom(job_to_test, key) == expected_count


class TestDefaultBronzeAdHocJob:
    def test_additional_parameter(self, bronze_adhoc_job: dict, working_dir_of_current_file):
        add_pams = glom.glom(bronze_adhoc_job, SPARK_PYTHON_TASK["parameters"])
        assert {
                add_pams[2]: add_pams[3],
                add_pams[4]: add_pams[5],
            } == {
                "--secrets-config-location": f"{SHARED_CONFIG_DIR}/secrets_config.json",
                "--kafka-config-location": f"{SHARED_CONFIG_DIR}/kafka_config.json",
            }

    @pytest.mark.parametrize("expected_library", ["glom", "spooq", "pyyaml"])
    def test_libraries(self, expected_library: str, bronze_adhoc_job: dict):
        defined_libraries = [
            lib.split(" == ")[0] for lib in glom.glom(bronze_adhoc_job, "tasks.0.libraries.*.pypi.package")
        ]
        assert expected_library in defined_libraries


class TestDefaultBronzeSilverGoldJob:
    def test_job_name(self, bronze_silver_gold_job: CustomizedJob):
        assert glom.glom(bronze_silver_gold_job, "name") == "Bronze Silver Gold: Test Entity"

    @pytest.mark.parametrize(
        argnames=["key", "expected_value"],
        argvalues=[
            (JOB_SCHEDULE["timezone_id"], "Europe/Vienna"),
            (JOB_SCHEDULE["quartz_cron_expression"], "0 0 1 ? * *"),
            (JOB_SCHEDULE["pause_status"], "UNPAUSED"),
        ],
    )
    def test_schedule(self, key: TType, expected_value: str, bronze_silver_gold_job: CustomizedJob):
        assert glom.glom(bronze_silver_gold_job, key) == expected_value

    @pytest.mark.parametrize(
        ["key", "expected_tag"],
        # fmt: off
        [
            (JOB_TAGS["entity_group"], "test_entity_group"),
            (JOB_TAGS["entity"],       "test_entity"),
            (JOB_TAGS["layer"],        "bronze_silver_gold"),
        ]
        # fmt: on
    )
    def test_tags(self, key: TType, expected_tag: str, bronze_silver_gold_job: CustomizedJob):
        assert glom.glom(bronze_silver_gold_job, key) == expected_tag

    @pytest.mark.parametrize(
        argnames=["key", "expected_count"],
        argvalues=[
            (TASKS.__("len__")(), 3),
            (JOB_CLUSTERS.__("len__")(), 3),
        ],
    )
    def test_counts(self, key: TType, expected_count: int, bronze_silver_gold_job: CustomizedJob):
        assert glom.glom(bronze_silver_gold_job, key) == expected_count

    @pytest.mark.parametrize(
        # fmt: off
        argnames=[
            "task_position",  "layer",   "depends_on",            "permission_group"
        ],
        argvalues=[
            (2,               "bronze",  [],                      "etl"),
            (1,               "silver",  ["bronze_test_entity"],  "etl"),
            (0,               "gold",    ["silver_test_entity"],  "etl"),
        ],
        ids=["bronze_task", "silver_task", "gold_task"]
        # fmt: on
    )
    class TestBronzeSilverGoldTasks:
        @pytest.fixture()
        def task_to_test(
            self,
            bronze_silver_gold_job: CustomizedJob,
            task_position: int,
            layer: str,
            depends_on: str,
            permission_group: str,
        ) -> TType:
            return glom.glom(bronze_silver_gold_job, TASKS[task_position])

        @pytest.fixture()
        def python_task_to_test(
            self, task_to_test: TType, task_position: int, layer: str, depends_on: str, permission_group: str
        ) -> TType:
            return task_to_test["spark_python_task"]

        def test_task_key(
            self,
            bronze_silver_gold_job: CustomizedJob,
            task_to_test: TType,
            task_position: int,
            layer: str,
            depends_on: str,
            permission_group: str,
        ):
            assert task_to_test.get("task_key") == f"{layer}_test_entity"

        def test_job_cluster_key(
            self,
            bronze_silver_gold_job: CustomizedJob,
            task_to_test: TType,
            task_position: int,
            layer: str,
            depends_on: str,
            permission_group: str,
        ):
            assert task_to_test.get("job_cluster_key") == f"cluster_test_entity_{permission_group}_{layer}"

        @pytest.mark.parametrize(
            ["key", "expected_value"],
            # fmt: off
            [
                (T["python_file"],   "{cwd}/task_{layer}/pipeline_runner.py"),
                (T["parameters"][0], "PRD"),
                (T["parameters"][1], "{cwd}/task_{layer}/databricks_config.json"),
            ]
            # fmt: on
        )
        def test_python_task(
            self,
            python_task_to_test: TType,
            key: str,
            expected_value: str,
            task_position: int,
            layer: str,
            depends_on: str,
            permission_group: str,
            working_dir_of_current_file: str,
        ):
            assert glom.glom(python_task_to_test, key) == expected_value.format(
                cwd=working_dir_of_current_file, layer=layer
            )

        @pytest.mark.parametrize("expected_library", ["glom", "spooq"])
        def test_libraries(
            self,
            task_to_test: dict,
            expected_library: str,
            task_position: int,
            layer: str,
            depends_on: str,
            permission_group: str,
        ):
            defined_libraries = [lib.split(" == ")[0] for lib in glom.glom(task_to_test, "libraries.*.pypi.package")]
            assert expected_library in defined_libraries

        def test_max_retries(
            self, task_to_test: dict, task_position: int, layer: str, depends_on: str, permission_group: str
        ):
            assert glom.glom(task_to_test, "max_retries") == 1

        def test_dependencies(
            self, task_to_test: dict, task_position: int, layer: str, depends_on: str, permission_group: str
        ):
            assert glom.glom(task_to_test, "depends_on.*.task_key") == depends_on

    @pytest.mark.parametrize(
        # fmt: off
        argnames=[
            "cluster_position",  "layer",   "permission_group"
        ],
        argvalues=[
            (2,                  "bronze",  "etl"),
            (1,                  "silver",  "etl"),
            (0,                  "gold",    "etl"),
        ],
        ids=["bronze_task", "silver_task", "gold_task"]
        # fmt: on
    )
    class TestBronzeSilverGoldJobClusters:
        @pytest.fixture()
        def job_cluster_to_test(
            self, bronze_silver_gold_job: CustomizedJob, cluster_position: int, layer: str, permission_group: str
        ) -> TType:
            return glom.glom(bronze_silver_gold_job, JOB_CLUSTERS[cluster_position])

        @pytest.fixture()
        def new_cluster_to_test(
            self, job_cluster_to_test: dict, cluster_position: int, layer: str, permission_group: str
        ) -> TType:
            return job_cluster_to_test.get("new_cluster")

        def test_job_cluster_key(
            self,
            bronze_silver_gold_job: CustomizedJob,
            job_cluster_to_test: TType,
            cluster_position: int,
            layer: str,
            permission_group: str,
        ):
            assert job_cluster_to_test.get("job_cluster_key") == f"cluster_test_entity_{permission_group}_{layer}"

        def test_num_workers(self, new_cluster_to_test: dict, cluster_position: int, layer: str, permission_group: str):
            assert new_cluster_to_test.get("num_workers") == 0

        @pytest.mark.parametrize(
            ["key", "expected_value"],
            # fmt: off
            [
                (T["spark_version"],                 SPARK_VERSION),
                (T["runtime_engine"],                "STANDARD"),
                (T["node_type_id"],                  "m5dn.xlarge"),
                (T["driver_node_type_id"],           "m5dn.xlarge"),
                (T["custom_tags"]["layer"],          "{layer}"),
                (T["custom_tags"]["entity_group"],   "test_entity_group"),
                (T["custom_tags"]["entity"],         "test_entity"),
                (T["custom_tags"]["ResourceClass"],  "SingleNode"),
            ]
            # fmt: on
        )
        def test_new_cluster(
            self,
            key: TType,
            expected_value: str,
            new_cluster_to_test: dict,
            cluster_position: int,
            layer: str,
            permission_group: str,
        ):
            assert glom.glom(new_cluster_to_test, key) == expected_value.format(layer=layer)

        @pytest.mark.parametrize(
            "expected_key",
            # fmt: off
            [
                "spark.master",
                "spark.databricks.cluster.profile",
            ]
            # fmt: on
        )
        def test_spark_configs(
            self, expected_key: str, new_cluster_to_test: dict, cluster_position: int, layer: str, permission_group: str
        ):
            assert expected_key in glom.glom(new_cluster_to_test, "spark_conf")


class TestNonStandardJob:
    @pytest.fixture(scope="class")
    def shared_parameters(self, working_dir_of_current_file: str) -> dict:
        return dict(entity_group="user", entity_name="identity", working_dir=working_dir_of_current_file)

    @pytest.fixture(scope="class")
    def custom_config(self) -> dict:
        return {
            "cluster": {
                "node_type_id": EnvironmentConfiguration(
                    environments_map={Env.STG: AWSClusterNodeType.GeneralPurpose.m5dn_xlarge},
                    default=AWSClusterNodeType.GeneralPurpose.m5dn_2xlarge,
                ),
                "custom_spark_conf": {"spark.sql.shuffle.partitions": "true"},
            },
            "task": {"additional_libraries": [Lib.pika]},
        }

    @pytest.fixture(scope="class")
    def custom_config_gold_dedup_legacy_user_id(self, custom_config: dict) -> dict:
        return {
            "job_name": "Gold: Identity - Deduplicated By legacy_user_id",
            "task": {
                "task_key": "gold_identity_deduplicated_by_legacy_user_id",
                "task_folder": "task_gold_deduplicated_by_legacy_user_id",
                **custom_config["task"],
            },
            "cluster": {
                "job_cluster_key": "cluster_identity_etl_gold_deduplicated_by_legacy_user_id",
                **custom_config["cluster"],
            },
        }

    @pytest.fixture(scope="class")
    def identity_job(
        self, custom_config: dict, custom_config_gold_dedup_legacy_user_id: dict, shared_parameters: dict
    ) -> dict:
        bronze_job = generate_single_task_job(layer="bronze", custom_config=custom_config, **shared_parameters)
        silver_job = generate_single_task_job(layer="silver", custom_config=custom_config, **shared_parameters)
        gold_job = generate_single_task_job(layer="gold", custom_config=custom_config, **shared_parameters)
        gold_job_dedup_legacy_user_id = generate_single_task_job(
            layer="gold", custom_config=custom_config_gold_dedup_legacy_user_id, **shared_parameters
        )

        return combine_single_task_jobs(
            layer="bronze_silver_gold+",
            entity_group=shared_parameters["entity_group"],
            entity_name=shared_parameters["entity_name"],
            jobs=[bronze_job, silver_job, gold_job, gold_job_dedup_legacy_user_id],
            dependency_mapping={
                gold_job_dedup_legacy_user_id.name.default: [silver_job.name.default],
                gold_job.name.default: [silver_job.name.default],
                silver_job.name.default: [bronze_job.name.default],
                bronze_job.name.default: None,
            },
        ).resolve(Env.PRD)

    def test_job_name(self, identity_job: dict):
        assert glom.glom(identity_job, "name") == "Bronze Silver Gold+: Identity"

    def test_schedule(self, identity_job: dict):
        assert glom.glom(identity_job, JOB_SCHEDULE) == {
            "timezone_id": "Europe/Vienna",
            "quartz_cron_expression": "0 0 1 ? * *",
            "pause_status": "UNPAUSED",
        }

    def test_job_tags(self, identity_job: dict):
        assert glom.glom(identity_job, JOB_TAGS) == {
            "entity_group": "user",
            "entity": "identity",
            "layer": "bronze_silver_gold+",
        }

    @pytest.mark.parametrize(
        argnames=["key", "expected_count"],
        argvalues=[
            (TASKS.__("len__")(), 4),
            (JOB_CLUSTERS.__("len__")(), 4),
        ],
    )
    def test_counts(self, key: TType, expected_count: int, identity_job: dict):
        assert glom.glom(identity_job, key) == expected_count

    def test_task_keys(self, identity_job: dict):
        assert glom.glom(identity_job, "tasks.*.task_key") == [
            "gold_identity_deduplicated_by_legacy_user_id",
            "gold_identity",
            "silver_identity",
            "bronze_identity",
        ]

    @pytest.mark.parametrize(
        "task_key",
        ["gold_identity_deduplicated_by_legacy_user_id", "gold_identity", "silver_identity", "bronze_identity"],
    )
    def test_libraries(self, task_key: str, identity_job: dict):
        task_to_test = glom.glom(
            identity_job, ("tasks", [glom.Check("task_key", equal_to=task_key, default=glom.SKIP)], "0")
        )
        defined_libraries = [lib.split(" == ")[0] for lib in glom.glom(task_to_test, "libraries.*.pypi.package")]
        assert {"spooq", "glom", "pika"}.issubset(defined_libraries)

    def test_job_cluster_keys(self, identity_job: dict):
        assert glom.glom(identity_job, "tasks.*.job_cluster_key") == [
            "cluster_identity_etl_gold_deduplicated_by_legacy_user_id",
            "cluster_identity_etl_gold",
            "cluster_identity_etl_silver",
            "cluster_identity_etl_bronze",
        ]

    @pytest.mark.parametrize(
        "cluster_key",
        [
            "cluster_identity_etl_gold_deduplicated_by_legacy_user_id",
            "cluster_identity_etl_gold",
            "cluster_identity_etl_silver",
            "cluster_identity_etl_bronze",
        ],
    )
    def test_custom_spark_configs(self, cluster_key: str, identity_job: dict):
        spark_conf = glom.glom(
            identity_job,
            (
                "job_clusters",
                [glom.Check("job_cluster_key", equal_to=cluster_key, default=glom.SKIP)],
                "0.new_cluster.spark_conf",
            ),
        )
        assert spark_conf.get("spark.sql.shuffle.partitions") == "true"

    def test_dependencies(self, identity_job: dict):
        assert flatten(glom.glom(identity_job, "tasks.*.depends_on.*.task_key")) == [
            "silver_identity",
            "silver_identity",
            "bronze_identity",
        ]
