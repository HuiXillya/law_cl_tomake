import logging
from src.db_scripts.db_init import DB_SCHEMA, TASKS_TABLE_NAME, _qname
from src.db_scripts.db_utility import get_db_connection, fetch_all_as_dict, fetch_one_as_dict

logger = logging.getLogger(__name__)

def create_task(task_id: str) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            qname = _qname(DB_SCHEMA, TASKS_TABLE_NAME)
            cursor.execute(f"INSERT INTO {qname} (task_id, status) VALUES (?, 0)", (task_id,))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"create_task failed: {e}")
        return False

def get_task_status(task_id: str) -> int:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            qname = _qname(DB_SCHEMA, TASKS_TABLE_NAME)
            cursor.execute(f"SELECT status FROM {qname} WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return -999 # Not found
    except Exception as e:
        logger.error(f"get_task_status failed: {e}")
        return -999

def get_pending_tasks() -> list:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            qname = _qname(DB_SCHEMA, TASKS_TABLE_NAME)
            cursor.execute(f"SELECT task_id, status, created_at, remark FROM {qname} WHERE status = 0 ORDER BY created_at DESC")
            return fetch_all_as_dict(cursor)
    except Exception as e:
        logger.error(f"get_pending_tasks failed: {e}")
        return []

def get_approved_tasks() -> list:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            qname = _qname(DB_SCHEMA, TASKS_TABLE_NAME)
            cursor.execute(f"SELECT task_id, status, created_at, remark FROM {qname} WHERE status = 1 ORDER BY created_at DESC")
            return fetch_all_as_dict(cursor)
    except Exception as e:
        logger.error(f"get_approved_tasks failed: {e}")
        return []

def get_task_by_id(task_id: str) -> dict:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            qname = _qname(DB_SCHEMA, TASKS_TABLE_NAME)
            cursor.execute(f"SELECT task_id, status, created_at, remark FROM {qname} WHERE task_id = ?", (task_id,))
            return fetch_one_as_dict(cursor)
    except Exception as e:
        logger.error(f"get_task_by_id failed: {e}")
        return None

def get_task_messages(task_id: str) -> list:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            from src.db_scripts.db_init import TABLE_NAME
            qname = _qname(DB_SCHEMA, TABLE_NAME)
            cursor.execute(f"SELECT * FROM {qname} WHERE task_id = ?", (task_id,))
            return fetch_all_as_dict(cursor)
    except Exception as e:
        logger.error(f"get_task_messages failed: {e}")
        return []

def approve_task_transaction(task_id: str, messages_updates: list) -> bool:
    """
    Updates task status to 1 and updates multiple messages in a single transaction.
    messages_updates: list of dicts with {'id': msg_id, 'departments': [], 'cc_departments': []}
    Note: This function no longer updates message-level remark; task-level remark is handled separately.
    """
    import json
    from src.db_scripts.db_init import TABLE_NAME
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Update Task Status
            tasks_qname = _qname(DB_SCHEMA, TASKS_TABLE_NAME)
            cursor.execute(f"UPDATE {tasks_qname} SET status = 1 WHERE task_id = ?", (task_id,))
            
            # 2. Update Messages (departments and cc_departments only)
            msg_qname = _qname(DB_SCHEMA, TABLE_NAME)
            for update in messages_updates:
                dept_json = json.dumps(update['departments'])
                cc_dept_json = json.dumps(update['cc_departments'])
                cursor.execute(
                    f"UPDATE {msg_qname} SET departments = ?, cc_departments = ? WHERE id = ?",
                    (dept_json, cc_dept_json, update['id'])
                )
            
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"approve_task_transaction failed: {e}")
        return False

def update_task_status(task_id: str, status: int) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            qname = _qname(DB_SCHEMA, TASKS_TABLE_NAME)
            
            cursor.execute(f"UPDATE {qname} SET status = ? WHERE task_id = ?", (status, task_id))
            conn.commit()  # Commit transaction
            return True
    except Exception as e:
        logger.error(f"update_task_status failed: {e}")
        return False

def update_task_remark(task_id: str, remark: str) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            qname = _qname(DB_SCHEMA, TASKS_TABLE_NAME)
            
            # Append to existing remark if any
            cursor.execute(f"SELECT remark FROM {qname} WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            current_remark = row[0] if row and row[0] else ""
            new_remark = f"{current_remark}; {remark}" if current_remark else remark
            
            cursor.execute(f"UPDATE {qname} SET remark = ? WHERE task_id = ?", (new_remark, task_id))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"update_task_remark failed: {e}")
        return False
