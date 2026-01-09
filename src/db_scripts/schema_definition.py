
TABLE_DEFINITIONS = {
    "approval_tasks": {
        "columns": [
            {"name": "task_id", "type": "VARCHAR(64)", "constraints": "PRIMARY KEY"},
            {"name": "status", "type": "INT", "constraints": "DEFAULT 0"},
            {"name": "remark", "type": "NVARCHAR(MAX)", "constraints": ""},
            {"name": "created_at", "type": "DATETIME2", "constraints": "DEFAULT SYSDATETIME()"}
        ],
        "indexes": [
            {"name": "idx_tasks_status_created", "columns": ["status", "created_at DESC"]}
        ]
    },
    "messages": {
        "columns": [
            {"name": "id", "type": "INT", "constraints": "IDENTITY PRIMARY KEY"},
            {"name": "title", "type": "NVARCHAR(MAX)", "constraints": ""},
            {"name": "date", "type": "DATETIME2", "constraints": ""},
            {"name": "link", "type": "NVARCHAR(MAX)", "constraints": ""},
            {"name": "departments", "type": "NVARCHAR(MAX)", "constraints": ""},
            {"name": "cc_departments", "type": "NVARCHAR(MAX)", "constraints": ""},
            {"name": "looked", "type": "BIT", "constraints": ""},
            {"name": "sended", "type": "BIT", "constraints": ""},
            {"name": "title_hash", "type": "NVARCHAR(64)", "constraints": ""},
            {"name": "datetime", "type": "DATETIME2", "constraints": ""},
            {"name": "documentNumber", "type": "NVARCHAR(64)", "constraints": ""},
            {"name": "displaySiteName", "type": "NVARCHAR(64)", "constraints": ""},
            {"name": "content", "type": "NVARCHAR(MAX)", "constraints": ""},
            {"name": "task_id", "type": "VARCHAR(64)", "constraints": ""},
            {"name": "attachments", "type": "NVARCHAR(MAX)", "constraints": ""}
        ],
        "foreign_keys": [
            {"column": "task_id", "references": "approval_tasks(task_id)"}
        ],
        "indexes": [
            {"name": "idx_title_hash", "columns": ["title_hash"]},
            {"name": "idx_msg_task_id", "columns": ["task_id"]}
        ]
    }
}
