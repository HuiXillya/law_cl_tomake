import logging
from src.htmx_gen import gen_result_table, polling_wrapper, no_polling_wrapper
from src.string_management import TasksKey, TaskStatus

logger = logging.getLogger(__name__)
def step3_result(task_id,tasks):
    if not task_id in tasks:
        for k in tasks.keys():
            logger.debug(f"Existing task IDs: {k}")
        logger.error(f"Requested task ID: {task_id} not found.")
        return  "<p>Task ID not found.</p>"
    status = tasks[task_id].get(TasksKey.STATUS.value, TaskStatus.UNKNOWN)
    logger.info(f"Current status for task {task_id}: {status}")
    if status == TaskStatus.UNKNOWN:
        logger.warning("Task status is unknown.")
        return "<p>Task status is unknown.</p>"
    elif status == TaskStatus.STEP3_PROCESSING:
        loading_str = _loaging(tasks[task_id])
        rt = loading_str + gen_result_table(polling_wrapper, task_id, tasks[task_id].get(TasksKey.ANNOUNCEMENTS.value, []))
        return rt
    elif status == TaskStatus.STEP3_COMPLETED:
        rt = gen_result_table(no_polling_wrapper, task_id, tasks[task_id].get(TasksKey.ANNOUNCEMENTS.value, []))
        return rt
    else:
        logger.error(f"Task {task_id} is in an unexpected status: {status}")
        return f"<p>Task is in an unexpected status: {status}</p>"

def _loaging(task):
    raw_rt = task.setdefault(TasksKey.LOADING.value, "Loading...")
    if len(raw_rt) < 10:
        raw_rt += "." 
        task[TasksKey.LOADING.value] = raw_rt
    else:
        task[TasksKey.LOADING.value] = "Loading"
    return "<p>" + raw_rt + "</p>"