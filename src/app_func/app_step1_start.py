from fastapi import FastAPI, BackgroundTasks, Request
import asyncio
import uuid
import time
from src.app_func.app_step1_init import _get_all_crawlers
from src.string_management import TasksKey, TaskStatus
from src.app_func.crawler_caller import run_crawlers_step1

async def step1_start(request: Request,background_tasks: BackgroundTasks,tasks: dict):
    form_data = await request.form()
    selected_crawlers = form_data.getlist("selectedOptions")
    
    # Generate a unique task ID
    task_id = str(uuid.uuid4())
    clr_list = _get_all_crawlers()
    clrn2clrdict = {clr.__name__: clr for clr in clr_list}

    # Store the task with initial status
    tasks[task_id] = {
        TasksKey.STATUS.value: TaskStatus.CRAWLING,
        "selected_crawlers": list(map(lambda x:clrn2clrdict[x],selected_crawlers)),
        "last_beat": time.time(),
        TasksKey.ANNOUNCEMENTS.value: []
    }
    
    # Start the crawling process in the background
    background_tasks.add_task(run_crawlers_step1, tasks[task_id])
    
    return task_id