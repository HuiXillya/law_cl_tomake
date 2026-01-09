
from src.string_management import URLS, TasksKey, AnnKey


def gen_datatable(task_id: str,new_anns: list[dict],old_anns: list[dict]) -> str:
    ann_wrappers = ''
    for new_ann,old_ann in zip(new_anns, old_anns): 
        # old_ann will be empty dict if not exist in DB
        if not new_ann.get(AnnKey.LOOKED.value,False) and len(old_ann)>0: 
            continue
        on_row_text = _gen_single_row_with_old_ann(task_id,new_ann,old_ann) \
            if old_ann else _gen_single_row_newann_only(task_id,new_ann)
        ann_wrappers += f'''
        <div class="one-ann-wrapper">
        <detail class="one-ann-detail" open>
            <summary class="one-ann-summary">
                <a href="{new_ann[AnnKey.LINK.value]}" target="_blank">
                {new_ann[AnnKey.TITLE.value]} - {new_ann[AnnKey.DATE.value]} </a>
            </summary>
            {on_row_text}
        </detail>
        </div>
        '''
    
    submit_button = f'''
    <div style="margin-top: 20px; text-align: center;">
        <button hx-get="{URLS.SAVE_TO_DB.value}?{TasksKey.TASK_ID.value}={task_id}" 
                hx-swap="outerHTML"
                hx-trigger="click"
                style="padding: 10px 20px; font-size: 16px; background-color: #4CAF50; color: white; border: none; cursor: pointer;">
                送出簽核單 (Submit for Approval)
        </button>
    </div>
    '''

    total_wrapper = '''
        <div class="all-ann-wrapper">
        {content}
        </div>
        {submit_button}
        '''
    return total_wrapper.format(content=ann_wrappers, submit_button=submit_button)

def _gen_save_button(task_id: str, ann_idx: str,autosave: bool) -> str:
    # Deprecated
    return ""
def gen_saved_label() -> str:
    return '<span>已儲存至資料庫</span>'
def _gen_single_row_with_old_ann(task_id,new_ann: dict,old_ann: dict):
    n_date, n_title, n_link , n_dept_list, n_cc_list, n_looked, n_sended = \
        _unbox_ann(new_ann).values()
    o_date, o_title, o_link , o_dept_list, o_cc_list, o_looked, o_sended = \
        _unbox_ann(old_ann).values()
    
    task_status = old_ann.get('task_status')
    old_task_id = old_ann.get('task_id', 'Unknown')
    warning_msg = ""
    if task_status == 1:
        warning_msg = f'<div style="color: red; font-weight: bold;">(警告：此公告已於任務 {old_task_id} 中核准)</div>'
    elif task_status == 2:
        warning_msg = f'<div style="color: red; font-weight: bold;">(警告：此公告已於任務 {old_task_id} 中完成)</div>'

    dept_display_str = f'<li><b>部門</b>: {o_dept_list} ➔ {n_dept_list}</li>' if _list_should_display(o_dept_list, n_dept_list) else ''
    cc_display_str = f'<li><b>副本部門</b>: {o_cc_list} ➔ {n_cc_list}</li>' if _list_should_display(o_cc_list, n_cc_list) else ''
    return f'''
    <ul class="one-ann-dept-list">
    <span class="newdata" style="color: red;">(Rewrite!!)</span>
        {warning_msg}
        {dept_display_str}
        {cc_display_str}
        <li><b>已讀</b>:
                {'已讀' if o_looked else '未讀'} ➔ {_gen_checkbox(task_id, new_ann.get(AnnKey.IDX.value,'0'), AnnKey.LOOKED.value, n_looked)}
        </li>
        <li><b>已發送</b>:
                {'已發送' if o_sended else '未發送'} ➔ {_gen_checkbox(task_id, new_ann.get(AnnKey.IDX.value,'0'), AnnKey.SENDED.value, n_sended)}    
        </li>
'''
def _list_should_display(old: list, new: list)-> bool:
    if len(new) == 0:
        return False
    if sorted(old) != sorted(new):
        return True
def _gen_single_row_newann_only(task_id,ann: dict) -> str:
    date, title, link , dept_list, cc_list, looked, sended = \
        _unbox_ann(ann).values()
    return f'''
    <ul class="one-ann-dept-list">
    <span class="newdata" style="color: green;">(New!!)</span>
        <li><b>日期</b>: {date}</li>
        <li><b>標題</b>: <a href="{link}" target="_blank">{title}</a></li>
        {f'<li><b>部門</b>: {dept_list}</li>' if dept_list != '[]' else ''}
        {f'<li><b>副本部門</b>: {cc_list}</li>' if cc_list != '[]' else ''}
        <li><b>已讀</b>:
                {_gen_checkbox(task_id, ann.get(AnnKey.IDX.value,'0'), AnnKey.LOOKED.value, looked)}
        </li>
        <li><b>已發送</b>:
                {_gen_checkbox(task_id, ann.get(AnnKey.IDX.value,'0'), AnnKey.SENDED.value, sended)}
        </li>
    </ul>
    '''
def _gen_checkbox(task_id: str, ann_idx: str, checkbox_name: str, is_checked: bool) -> str:
    api_url = f"{URLS.ANN_CHECKBOX_SET.value}?{TasksKey.TASK_ID.value}={task_id}&ann_idx={ann_idx}&checkbox_name={checkbox_name}"
    display_str = '已讀' if checkbox_name == AnnKey.LOOKED.value else '已發送'
    return f'''
    <input type="checkbox" id="{checkbox_name}_{ann_idx}" name="{checkbox_name}" value="true"
        hx-swap="none"
        hx-patch="{api_url}" hx-trigger="change" {'checked' if is_checked else ''}>
    <label for="{checkbox_name}_{ann_idx}">{display_str}</label>
    '''
def _unbox_ann(ann: dict):
    return {
        AnnKey.DATE.value: ann.get(AnnKey.DATE.value,'(無日期)'),
        AnnKey.TITLE.value: ann.get(AnnKey.TITLE.value,'(無標題)'),
        AnnKey.LINK.value: ann.get(AnnKey.LINK.value,'#'),
        AnnKey.DEPARTMENTS.value: str(ann.get(AnnKey.DEPARTMENTS.value,[])),
        AnnKey.CC_DEPARTMENTS.value: str(ann.get(AnnKey.CC_DEPARTMENTS.value,[])),
        AnnKey.LOOKED.value: ann.get(AnnKey.LOOKED.value,False),
        AnnKey.SENDED.value: ann.get(AnnKey.SENDED.value,False)
    }