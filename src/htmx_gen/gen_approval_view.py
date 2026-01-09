from src.string_management import URLS, AnnKey
from src.utils.department_provider import get_department_names

# Load department list (will raise on JSON errors or missing file)
department_list = get_department_names()

def gen_task_list(tasks: list) -> str:
    if not tasks:
        return "<div style='padding: 20px;'>No pending tasks.</div>"
        
    html = "<div style='padding: 20px;'><h2>Pending Approvals</h2><ul class='task-list'>"
    for task in tasks:
        remark_html = f"<br><strong>Remark:</strong> {task['remark']}" if task.get('remark') else ""
        html += f"""
        <li style='margin-bottom: 10px; padding: 10px; border: 1px solid #ccc;'>
            <strong>Task ID:</strong> {task['task_id']} <br>
            <strong>Created:</strong> {task['created_at']} 
            {remark_html} <br>
            <button hx-get="{URLS.APPROVAL_DETAIL.value}?task_id={task['task_id']}"
                    hx-target="#approval-detail-container"
                    style="margin-top: 5px; cursor: pointer;">
                Review
            </button>
        </li>
        """
    html += "</ul><div id='approval-detail-container' style='margin-top: 20px; border-top: 2px solid #333; padding-top: 20px;'></div></div>"
    return html

def gen_task_detail(task_id: str, messages: list, task_remark: str = "") -> str:
    html = f"<h3>Reviewing Task: {task_id}</h3>"
    if task_remark:
        html += f"<div style='margin-bottom:10px; padding:10px; background-color: #f9f9f9; border-left: 5px solid #2196F3;'><strong>Task LOG:</strong><br>{task_remark}</div>"
    
    # Approve/Reject buttons
    html += f"""
    <div style="margin-bottom: 20px;">
        <form hx-post="{URLS.APPROVAL_ACTION.value}" hx-target="#main-container">
            <input type="hidden" name="task_id" value="{task_id}">
            <button type="submit" name="action" value="approve" 
                    style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; margin-right: 10px;">
                Approve
            </button>
            <button type="submit" name="action" value="reject" 
                    style="background-color: #f44336; color: white; padding: 10px 20px; border: none; cursor: pointer;">
                Reject
            </button>
        </form>
    </div>
    """
    
    for msg in messages:
        html += _gen_message_row(msg, task_id)
        
    return html

def _gen_message_row(msg: dict, task_id: str) -> str:
    msg_id = msg.get('id')
    title = msg.get('title')
    link = msg.get('link')
    depts = msg.get('departments', [])
    cc_depts = msg.get('cc_departments', [])
    
    return f"""
    <div class="message-row" id="msg-row-{msg_id}" style="border: 1px solid #eee; padding: 10px; margin-bottom: 10px;">
        <div><a href="{link}" target="_blank">{title}</a></div>
        <div style="margin-top: 5px;">
            {_gen_dept_checkboxes(msg_id, depts, cc_depts, task_id)}
        </div>
    </div>
    """

def _gen_dept_checkboxes(msg_id, dept_list, cc_list, task_id):
    options_html = ""
    for dept_idx, dept_name in enumerate(department_list):
        to_checked = 'checked' if dept_name in dept_list else ''
        cc_checked = 'checked' if dept_name in cc_list else ''
        checked_attr = 'checked' if cc_checked or to_checked else ''
        
        option_html = f'''
        <div class="dept-option" style="display: inline-block; margin-right: 15px;">
            <input type="checkbox" {checked_attr}
                hx-vals='{{"data": "task_id:{task_id} msg_id:{msg_id} dept_idx:{dept_idx} type:check"}}'
                hx-patch="{URLS.APPROVAL_PATCH_DEPT.value}"
                hx-target="#msg-row-{msg_id}"
                hx-swap="outerHTML">
            <label>{dept_name}</label>
            <div class="recipient-type" style="display: inline-block; margin-left: 5px;">
                <input type="radio" name="dept_{msg_id}_{dept_idx}" 
                    value="task_id:{task_id} msg_id:{msg_id} dept_idx:{dept_idx} type:to" 
                    hx-patch="{URLS.APPROVAL_PATCH_DEPT.value}"
                    hx-target="#msg-row-{msg_id}"
                    hx-swap="outerHTML"
                    {to_checked}>
                <label>To</label>
                
                <input type="radio" name="dept_{msg_id}_{dept_idx}" 
                    value="task_id:{task_id} msg_id:{msg_id} dept_idx:{dept_idx} type:cc" 
                    hx-patch="{URLS.APPROVAL_PATCH_DEPT.value}"
                    hx-target="#msg-row-{msg_id}"
                    hx-swap="outerHTML"
                    {cc_checked}>
                <label>CC</label>
            </div>
        </div>
        '''
        options_html += option_html
    return options_html
