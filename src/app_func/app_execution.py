from fastapi import Request
from src.db_scripts.task_manager import get_approved_tasks, get_task_messages, update_task_status, get_task_by_id
from src.htmx_gen import gen_execution_view

def execution_list() -> str:
    tasks = get_approved_tasks()
    return gen_execution_view.gen_task_list(tasks)

async def execution_action(request: Request) -> str:
    # Can be GET (detail) or POST (done)
    if request.method == 'GET':
        task_id = request.query_params.get('task_id')
        messages = get_task_messages(task_id)
        task = get_task_by_id(task_id)
        remark = task.get('remark', '') if task else ''
        return gen_execution_view.gen_execution_detail(task_id, messages, remark)
    elif request.method == 'POST':
        form = await request.form()
        task_id = form.get('task_id')
        action = form.get('action')
        
        if action == 'done':
            update_task_status(task_id, 2)
            
        return execution_list()
