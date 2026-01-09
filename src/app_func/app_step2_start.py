import time
from fastapi import FastAPI, BackgroundTasks, Request

from src.app_func.crawler_caller import announcement_crawler_process
from src.string_management import TasksKey, TaskStatus
async def step2_start(background_tasks: BackgroundTasks,task_id: str,tasks: dict):
    if task_id not in tasks:
        return {"error": "Invalid task ID"}
    
    task = tasks[task_id]
    __check_task_keys(task)
    if task[TasksKey.STATUS.value] != TaskStatus.SELECTING:
        return {"error": "Task is not in a valid state to start step 2"}
    # Update task status
    task[TasksKey.STATUS.value] = TaskStatus.STEP3_PROCESSING
    task["last_beat"] = time.time()
    background_tasks.add_task(announcement_crawler_process,task_id, tasks)
    return {"message": "Step 2 started"}

def __check_task_keys(task: dict) -> bool:
    required_keys = [TasksKey.STATUS.value, 'selected_crawlers', 'last_beat']
    for key in required_keys:
        if key not in task:
            raise KeyError(f"Task is missing required key: {key}")
    return True