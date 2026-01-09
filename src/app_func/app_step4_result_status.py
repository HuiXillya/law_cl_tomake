from src.db_scripts.message_manager import get_data_by_title
from src.db_scripts.task_manager import get_task_status
from src.htmx_gen import gen_datatable
from src.string_management import TasksKey, AnnKey, TaskStatus
def step4_result_status(tasks_id,tasks) ->str:
    if not tasks_id in tasks:
        return "No task found."
    task = tasks[tasks_id]
    if task[TasksKey.STATUS.value] != TaskStatus.STEP3_COMPLETED:
        return "Task not completed yet. Please wait."
    all_anns = task.get(TasksKey.ANNOUNCEMENTS.value, [])
    
    # Filter selected announcements only
    anns = [ann for ann in all_anns if ann.get(AnnKey.SELECTED.value, False)]
    
    if not anns:
        return "<div class='error' style='text-align: center; margin-top: 20px;'>No announcements selected. Please go back to Step 2.</div>"

    anns_in_db = []
    for ann in anns:
        db_ann = get_data_by_title(ann[AnnKey.TITLE.value])
        if db_ann and db_ann.get('task_id'):
            db_ann['task_status'] = get_task_status(db_ann['task_id'])
        anns_in_db.append(db_ann)

    for ann in anns:
        ann[AnnKey.LOOKED.value] = ann.get(AnnKey.SELECTED.value, False)
        ann[AnnKey.SENDED.value] = bool(ann.setdefault(AnnKey.DEPARTMENTS.value, []))
    return gen_datatable(tasks_id, anns, anns_in_db)


    