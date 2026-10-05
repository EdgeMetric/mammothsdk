"""Worked examples of an automation, one per kind of task, as the create route takes them.

Copied from the create route's own documented examples: the server keeps them
beside the route, where a client that only speaks to the API cannot read them.
"""

from .sdk import JsonValue

AUTOMATION_EXAMPLES: list[dict[str, JsonValue]] = [
    {
        "name": "Data Consolidation Orchestration",
        "description": "Data Consolidation Orchestration",
        "tasks": [
            {
                "task_type": "append_data",
                "details": {
                    "destination_dataset_ids": [6],
                    "source_folder_resource_id": 1,
                },
                "conditions": [
                    {
                        "condition_type": "new_data_addition_in_folder",
                        "details": {"file_contains": "less"},
                    }
                ],
            }
        ],
    },
    {
        "name": "Data Refresh Orchestration",
        "description": "Data Refresh Orchestration",
        "tasks": [
            {
                "task_type": "run_data_retrieval",
                "details": {
                    "ds_ids": [
                        {
                            "ds_id": 873,
                            "on_refresh_action": "replace",
                            "unique_sequence_column": {
                                "c_name": "ID",
                                "c_type": "numeric",
                            },
                        },
                        {
                            "ds_id": 32323,
                            "on_refresh_action": "replace",
                            "unique_sequence_column": {
                                "c_name": "Transaction " "ID",
                                "c_type": "numeric",
                            },
                        },
                    ]
                },
            }
        ],
        "conditions": [
            {
                "condition_type": "at_specific_time",
                "details": {
                    "interval": 1,
                    "frequency": "daily",
                    "start_at": "2025-10-17 10:11:00",
                },
            },
            {
                "condition_type": "run_config",
                "details": {"execution_mode": "parallel", "trigger_type": "schedule"},
            },
        ],
    },
    {
        "name": "Messaging Orchestration",
        "description": "Messaging Orchestration",
        "tasks": [
            {
                "task_type": "send_an_alert",
                "details": {
                    "alert_type": "email",
                    "subject": "test email alert",
                    "message": "This is for test",
                    "recipients": ["prajna.hegde@mammoth.io"],
                    "attachments": {"dataview_ids": [9]},
                    "test_email": False,
                },
            }
        ],
        "conditions": [
            {
                "condition_type": "at_specific_time",
                "details": {
                    "interval": 5,
                    "frequency": "minutely",
                    "start_now": True,
                    "start_at": "2025-09-26 10:39:00",
                    "until": "2025-09-27 10:00:00",
                },
            }
        ],
    },
    {
        "name": "File Collection Orchestration",
        "description": "File Collection Orchestration",
        "tasks": [
            {
                "task_type": "pull_cloud_files",
                "details": {
                    "connector_key": "google_drive",
                    "connection_key": "akdfjadfkjasdfjafds",
                    "connection_profile": [["mm-testing-bucket1"]],
                    "cloud_source_folder_path": {
                        "id": "35834kjksfakjdsf",
                        "path": "pattern",
                    },
                },
            }
        ],
        "conditions": [
            {
                "condition_type": "at_specific_time",
                "details": {
                    "interval": 5,
                    "frequency": "minutely",
                    "start_now": True,
                    "start_at": "2025-09-26 10:39:00",
                    "until": "2025-09-27 10:00:00",
                },
            },
            {
                "condition_type": "cloud_source_name_pattern",
                "details": {
                    "file_contains": "less",
                    "starts_with": "less",
                    "ends_with": "less",
                },
            },
        ],
    },
    {
        "name": "Data Retention Orchestration",
        "description": "Data Retention Orchestration",
        "tasks": [
            {
                "task_type": "apply_retention_policy",
                "details": {
                    "datasource_id": 555,
                    "rule_type": "time_based",
                    "threshold_value": 5,
                    "threshold_unit": "days",
                    "notify": True,
                    "notify_recipients": ["abc@gmail.com"],
                    "notify_trigger": "approval_and_policy_runs",
                    "require_approval": True,
                    "action": "suspend",
                },
            }
        ],
        "conditions": [
            {
                "condition_type": "at_specific_time",
                "details": {
                    "interval": 1,
                    "frequency": "daily",
                    "start_now": True,
                    "start_at": "2025-09-26 10:39:00",
                    "until": "2025-09-27 10:00:00",
                },
            }
        ],
    },
]
