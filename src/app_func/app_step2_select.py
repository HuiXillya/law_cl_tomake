import logging
from fastapi import Request
from src.string_management import TasksKey, AnnKey

logger = logging.getLogger(__name__)

async def set_selected_announcements(request: Request,tasks_id: str,tasks: dict) -> bool:
    if tasks_id not in tasks:
        logger.error(f"Task ID {tasks_id} not found in tasks.")
        return False
    task = tasks[tasks_id]
    form_data = await request.form()
    for k,v in form_data.items():
        ann_idx = int(k.replace('id-',''))
        if v == 'on':
            task[TasksKey.ANNOUNCEMENTS.value][ann_idx][AnnKey.SELECTED.value] = True
        else:
            task[TasksKey.ANNOUNCEMENTS.value][ann_idx][AnnKey.SELECTED.value] = False
async def set_selected_announcements_bydate(request: Request,tasks_id: str,tasks: dict) -> bool:
    if tasks_id not in tasks:
        logger.error(f"Task ID {tasks_id} not found in tasks.")
        return False
    task = tasks[tasks_id]
    form_data = await request.form()
    # form_data = str(form_data,encoding='utf-8')
    date_filter = form_data.get('select_date')
    for idx, ann in enumerate(task[TasksKey.ANNOUNCEMENTS.value]):
        ann_date = ann.get(AnnKey.DATE.value)
        if ann_date == date_filter:
            task[TasksKey.ANNOUNCEMENTS.value][idx][AnnKey.SELECTED.value] = not task[TasksKey.ANNOUNCEMENTS.value][idx].get(AnnKey.SELECTED.value,False)