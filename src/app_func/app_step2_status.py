from src.htmx_gen import gen_checkbox_table, gen_no_checkbox_table
from src.string_management import TasksKey, TaskStatus
def step2_status(task_id: str,tasks: dict,display_selected_only: bool=False):
    # return current status of the crawling task
    # if status == TaskStatus.CRAWLING return no checkbox table
    # if status == TaskStatus.SELECTING return checkbox table
    if task_id not in tasks:
        return "<p>Task ID not found</p>"
    task = tasks[task_id]
    if TasksKey.STATUS.value not in task:
        return "<p>Invalid task data</p>"
    if TasksKey.ANNOUNCEMENTS.value not in task:
        return "<p>No announcements found for this task</p>"
    
    status = task.get(TasksKey.STATUS.value)
    if status == TaskStatus.CRAWLING:
        return gen_no_checkbox_table(task_id,task.get(TasksKey.ANNOUNCEMENTS.value, []))
    elif status == TaskStatus.SELECTING:
        return gen_checkbox_table(task_id,task.get(TasksKey.ANNOUNCEMENTS.value, []),display_selected_only) 
    else:
        return gen_no_checkbox_table(task_id,task.get(TasksKey.ANNOUNCEMENTS.value, []),polling=False,seleted_only=True)