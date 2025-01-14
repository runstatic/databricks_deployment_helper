from databricks_deployment_helper.builders import set_task_new_cluster_from_job_clusters


def test_set_task_new_cluster_from_job_clusters():
    job = {
        "job_clusters": [
            {"job_cluster_key": "cluster1", "new_cluster": {"node_type": "node_type1"}},
            {"job_cluster_key": "cluster2", "new_cluster": {"node_type": "node_type2"}},
        ],
        "tasks": [
            {"task_key": "task_1", "job_cluster_key": "cluster1"},
            {"task_key": "task_2", "job_cluster_key": "cluster2"},
            {"task_key": "task_3", "new_cluster": {"node_type": "node_type3"}},
        ],
    }
    expected_job = {
        "tasks": [
            {"task_key": "task_1", "new_cluster": {"node_type": "node_type1"}},
            {"task_key": "task_2", "new_cluster": {"node_type": "node_type2"}},
            {"task_key": "task_3", "new_cluster": {"node_type": "node_type3"}},
        ]
    }
    assert set_task_new_cluster_from_job_clusters(job) == expected_job
