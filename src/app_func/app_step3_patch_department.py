import logging
from fastapi import Request
from src.utils.department_provider import get_department_names
from src.htmx_gen import gen_email_link
from src.string_management import TasksKey, AnnKey

# Load department list (will raise on JSON errors or missing file)
department_list = get_department_names()

logger = logging.getLogger(__name__)
async def patch_department_select(request: Request, task_id: str,tasks: dict) -> str:
    if task_id not in tasks:
        return "Invalid task ID"
    task = tasks[task_id]
    
    # Group selections by announcement index
    ann_selections = {} # {ann_idx: {'to': set(), 'cc': set(), 'all': set()}}
    
    form = await request.form()
    for _, v in form.items():
        # value format: ann_idx:{ann_idx} dept_idx:{dept_idx} type:{to|cc|outter}
        try:
            parts = v.split(" ")
            ann_idx = int(parts[0].split(":")[1])
            dept_idx = int(parts[1].split(":")[1])
            dept_type = parts[2].split(":")[1]
            
            if ann_idx not in ann_selections:
                ann_selections[ann_idx] = {'to': set(), 'cc': set(), 'all': set()}
            
            dept_name = department_list[dept_idx]
            if dept_type == 'outter':
                ann_selections[ann_idx]['all'].add(dept_name)
            elif dept_type == 'to':
                ann_selections[ann_idx]['to'].add(dept_name)
            elif dept_type == 'cc':
                ann_selections[ann_idx]['cc'].add(dept_name)
        except (IndexError, ValueError) as e:
            logger.debug(f"Error parsing form value '{v}': {e}")
            continue

    # Update task for each announcement found in form
    last_ann_idx = -1
    for ann_idx, selections in ann_selections.items():
        new_dept_selection = selections['to'] & selections['all']
        new_cc_selection = selections['cc'] & selections['all']
        
        task[TasksKey.ANNOUNCEMENTS.value][ann_idx][AnnKey.DEPARTMENTS.value] = list(new_dept_selection)
        task[TasksKey.ANNOUNCEMENTS.value][ann_idx][AnnKey.CC_DEPARTMENTS.value] = list(new_cc_selection)
        last_ann_idx = ann_idx

    if last_ann_idx == -1:
        return "No changes applied"

    # Return email link for the last processed announcement (maintaining original behavior but safer)
    target_ann = task[TasksKey.ANNOUNCEMENTS.value][last_ann_idx]
    title = target_ann[AnnKey.TITLE.value]
    content = target_ann[AnnKey.CONTENT.value]
    link = target_ann.get(AnnKey.LINK.value, '')
    full_content = f"{content}\n\nLink: {link}" if link else content
    
    return gen_email_link(
        set(target_ann[AnnKey.DEPARTMENTS.value]), 
        title, 
        full_content, 
        set(target_ann[AnnKey.CC_DEPARTMENTS.value])
    )
        
