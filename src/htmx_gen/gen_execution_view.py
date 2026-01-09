from src.string_management import URLS
from src.htmx_gen import gen_email_link

def gen_task_list(tasks: list) -> str:
    if not tasks:
        return "<div style='padding: 20px;'>No approved tasks pending execution.</div>"
        
    html = "<div style='padding: 20px;'><h2>Ready for Execution</h2><ul class='task-list'>"
    for task in tasks:
        remark_html = f"<br><strong>Remark:</strong> {task['remark']}" if task.get('remark') else ""
        html += f"""
        <li style='margin-bottom: 10px; padding: 10px; border: 1px solid #ccc;'>
            <strong>Task ID:</strong> {task['task_id']} <br>
            <strong>Created:</strong> {task['created_at']} 
            {remark_html} <br>
            <button hx-get="{URLS.EXECUTION_ACTION.value}?task_id={task['task_id']}"
                    hx-target="#execution-detail-container"
                    style="margin-top: 5px; cursor: pointer;">
                Execute (Send Emails)
            </button>
        </li>
        """
    html += "</ul><div id='execution-detail-container' style='margin-top: 20px; border-top: 2px solid #333; padding-top: 20px;'></div></div>"
    return html

def gen_execution_detail(task_id: str, messages: list, remark: str = "") -> str:
    html = f"<h3>Executing Task: {task_id}</h3>"
    
    if remark:
        html += f"<div style='margin-bottom: 15px; padding: 10px; background-color: #f9f9f9; border-left: 5px solid #2196F3;'><strong>Task LOG:</strong><br>{remark}</div>"

    # Mark as Done button
    html += f"""
    <div style="margin-bottom: 20px;">
        <form hx-post="{URLS.EXECUTION_ACTION.value}" hx-target="#main-container">
            <input type="hidden" name="task_id" value="{task_id}">
            <button type="submit" name="action" value="done" 
                    style="background-color: #2196F3; color: white; padding: 10px 20px; border: none; cursor: pointer;">
                Mark as Completed
            </button>
        </form>
    </div>
    """
    
    for msg in messages:
        html += _gen_email_row(msg)
        
    return html

def _gen_email_row(msg: dict) -> str:
    title = msg.get('title','')
    content = msg.get('content', '')
    link = msg.get('link', '')
    depts = msg.get('departments', []) or []
    cc_depts = msg.get('cc_departments', []) or []
    attachments = msg.get('attachments', []) or []

    # Append link to content for email body
    full_content = f"{content}\n\nLink: {link}" if link else content

    # gen_email_link expects lists of strings
    email_link = gen_email_link(depts, title, full_content, cc_depts)

    # prepare display strings
    to_text = ", ".join(depts) if depts else "無"
    cc_text = ", ".join(cc_depts) if cc_depts else "無"
    attachments_text = ", ".join(attachments) if attachments else "無"

    title_html = f'<a href="{link}" target="_blank">{title}</a>' if link else title

    return f"""
    <div class="message-row" style="border: 1px solid #eee; padding: 10px; margin-bottom: 10px;">
        <div><strong>{title_html}</strong></div>
        <div style="margin-top: 8px;"><strong>To:</strong> {to_text}</div>
        <div><strong>CC:</strong> {cc_text}</div>
        <div style="margin-top: 8px;"><strong>Attachments:</strong> {attachments_text}</div>
        <div style="margin-top: 10px;">
            {email_link}
            <span style="color:#666; font-size:0.9em; margin-left:10px;">（注意：mailto 無法自動附加檔案，請手動附檔）</span>
        </div>
    </div>
    """
