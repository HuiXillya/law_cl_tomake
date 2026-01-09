import logging
from src.db_scripts.task_manager import create_task, get_task_status, update_task_remark
from src.db_scripts.message_manager import insert_message_with_task, get_message_by_link, update_message_full
from src.db_scripts.db_init import SQL_CONNECTION_STRING
from src.htmx_gen import gen_saved_label
from src.string_management import TasksKey, AnnKey
import datetime
from mssql_python import connect

logger = logging.getLogger(__name__)

def save_to_db(task_id: str, tasks: dict) -> str:
    if not task_id in tasks:
        return "No task found."
    task = tasks[task_id]
    
    announcements = task.get(TasksKey.ANNOUNCEMENTS.value, [])
    
    # Check if there are any selected announcements
    has_selected = False
    for ann in announcements:
        if ann.get(AnnKey.SELECTED.value, False):
            has_selected = True
            break
            
    if not has_selected:
        return "<div class='error' style='color: red; font-weight: bold; text-align: center; margin-top: 20px;'>No announcements selected for approval.</div>"

    try:
        conn = connect(SQL_CONNECTION_STRING)
        cursor = conn.cursor()
        # Note: mssql-python/pymssql usually starts transaction automatically if autocommit=False (default)

        # Create Task
        if not create_task(task_id):
            raise Exception("Failed to create task in DB.")

        for ann in announcements:
            if not ann.get(AnnKey.SELECTED.value, False):
                continue

            link = ann.get(AnnKey.LINK.value)
            existing_msg = get_message_by_link(link)

            if existing_msg:
                old_task_id = existing_msg.get('task_id')
                if old_task_id:
                    old_status = get_task_status(old_task_id)
                    # If pending (0) or rejected (-1), take over.
                    if old_status in [0, -1]:
                        update_message_full(ann, task_id)
                    elif old_status in [1, 2]:
                        # Approved (1) or Done (2). Log to original task and take over.
                        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        log_msg = f"[Log] {now_str} 公告 \"{ann.get(AnnKey.TITLE.value)}\" 已重新送出至新任務 {task_id}"
                        update_task_remark(old_task_id, log_msg)
                        update_message_full(ann, task_id)
                    else:
                        # Unknown status, update anyway
                        update_message_full(ann, task_id)
                else:
                    # No task_id (legacy data?), update it.
                    update_message_full(ann, task_id)
            else:
                insert_message_with_task(ann, task_id)

        conn.commit()  # Commit transaction
        # Clear memory
        del tasks[task_id]
        
        return "<div class='success' style='color: green; font-weight: bold; text-align: center; margin-top: 20px;'>(Task Submitted)</div>"
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()  # Rollback transaction on error
        logger.error(f"save_to_db failed: {e}")
        return "<div class='error' style='color: red; font-weight: bold; text-align: center; margin-top: 20px;'>Failed to save task to DB.</div>"
    finally:
        if 'conn' in locals():
            conn.close()
