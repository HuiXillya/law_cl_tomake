from fastapi import Request
from src.db_scripts.task_manager import (
    get_pending_tasks, get_task_messages, update_task_status, 
    approve_task_transaction, update_task_remark, get_task_by_id
)
from src.db_scripts.message_manager import (
    get_message_by_id
)
from src.htmx_gen import gen_approval_view
from src.utils.department_provider import get_department_names

# Load department list (will raise on JSON errors or missing file)
department_list = get_department_names()

# Temporary storage for pending approvals
# Structure: {task_id: [msg1, msg2, ...]}
pending_approvals = {}

def approval_list() -> str:
    tasks = get_pending_tasks()
    return gen_approval_view.gen_task_list(tasks)

def approval_detail(task_id: str) -> str:
    # Load from DB to temporary storage
    messages = get_task_messages(task_id)
    pending_approvals[task_id] = messages
    task = get_task_by_id(task_id)
    task_remark = task.get('remark', '') if task else ''
    return gen_approval_view.gen_task_detail(task_id, messages, task_remark)

async def approval_action(request: Request) -> str:
    form = await request.form()
    task_id = form.get('task_id')
    action = form.get('action') # 'approve' or 'reject'
    
    if action == 'approve':
        if task_id in pending_approvals:
            modified_messages = pending_approvals[task_id]
            original_messages = get_task_messages(task_id)
            original_map = {m['id']: m for m in original_messages}
            
            updates = []
            change_logs = []
            for mod_msg in modified_messages:
                msg_id = mod_msg['id']
                orig_msg = original_map.get(msg_id)
                if not orig_msg:
                    continue
                
                # Compare departments
                orig_depts = set(orig_msg.get('departments', []))
                mod_depts = set(mod_msg.get('departments', []))
                orig_cc = set(orig_msg.get('cc_departments', []))
                mod_cc = set(mod_msg.get('cc_departments', []))
                
                changes = []
                # Check all departments for changes
                for dept_name in department_list:
                    prev_state = "None"
                    if dept_name in orig_depts: prev_state = "To"
                    elif dept_name in orig_cc: prev_state = "CC"
                    
                    new_state = "None"
                    if dept_name in mod_depts: new_state = "To"
                    elif dept_name in mod_cc: new_state = "CC"
                    
                    if prev_state != new_state:
                        changes.append(f"[{dept_name}: {prev_state} -> {new_state}]")
                
                if changes:
                    change_str = "; ".join(changes)
                    # Record per-message change log for task-level remark
                    change_logs.append(f"Msg {msg_id}: {change_str}")
                
                updates.append({
                    'id': msg_id,
                    'departments': list(mod_depts),
                    'cc_departments': list(mod_cc)
                })
            
            # Execute transaction (update message departments and task status)
            approve_task_transaction(task_id, updates)
            
            # Aggregate and save change logs to task remark (append)
            if change_logs:
                aggregated = "; ".join(change_logs)
                update_task_remark(task_id, aggregated)
            
    elif action == 'reject':
        update_task_status(task_id, -1)
        
    # Clear temporary storage
    if task_id in pending_approvals:
        del pending_approvals[task_id]
        
    return approval_list() # Refresh list

async def approval_patch_dept(request: Request) -> str:
    form = await request.form()
    if not form:
        return ""

    # Data format: "task_id:xxx msg_id:123 dept_idx:0 type:check"
    for k, v in form.items():
        try:
            parts = v.split(" ")
            task_id = parts[0].split(":")[1]
            msg_id = int(parts[1].split(":")[1])
            dept_idx = int(parts[2].split(":")[1])
            action_type = parts[3].split(":")[1]
        except (IndexError, ValueError):
            continue
        
        if task_id not in pending_approvals:
            # If not in cache, reload from DB
            pending_approvals[task_id] = get_task_messages(task_id)
            
        # Find the message in temporary storage
        msg = next((m for m in pending_approvals[task_id] if m['id'] == msg_id), None)
        if not msg:
            continue
            
        dept_name = department_list[dept_idx]
        current_depts = set(msg.get('departments', []))
        current_cc = set(msg.get('cc_departments', []))
        
        if action_type == 'to':
            current_depts.add(dept_name)
            if dept_name in current_cc:
                current_cc.remove(dept_name)
        elif action_type == 'cc':
            current_cc.add(dept_name)
            if dept_name in current_depts:
                current_depts.remove(dept_name)
        elif action_type == 'check':
            if dept_name in current_depts or dept_name in current_cc:
                if dept_name in current_depts:
                    current_depts.remove(dept_name)
                if dept_name in current_cc:
                    current_cc.remove(dept_name)
            else:
                current_depts.add(dept_name)
        
        # Update temporary storage
        msg['departments'] = list(current_depts)
        msg['cc_departments'] = list(current_cc)
        
        # Return updated message row HTML (using the cached data)
        return gen_approval_view._gen_message_row(msg, task_id)
        
    return ""
