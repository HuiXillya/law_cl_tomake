from src.string_management import TasksKey, AnnKey


def ann_checkbox_set(task_id :str,tasks,ann_idx :str,checkbox_name :str):
    if task_id not in tasks:
        return {"status":"error","message":"Task ID not found"}
    task = tasks[task_id]
    if TasksKey.ANNOUNCEMENTS.value not in task:
        return {"status":"error","message":"No announcements found for this task"}
    ann_list = task[TasksKey.ANNOUNCEMENTS.value]
    if len(ann_list) <= int(ann_idx):
        return {"status":"error","message":"Announcement index out of range"} 
    ann = ann_list[int(ann_idx)]
    valid_list = [AnnKey.LOOKED.value, AnnKey.SENDED.value, AnnKey.SELECTED.value]
    if checkbox_name not in valid_list:
        return {"status":"error","message":"Invalid checkbox name"}
    if checkbox_name not in ann:
        return {"status":"error","message":"Checkbox name not in announcement"}
    ann[checkbox_name] = not ann[checkbox_name]
    return {"status":"success","message":"Checkbox updated","new_value":ann[checkbox_name]}
        