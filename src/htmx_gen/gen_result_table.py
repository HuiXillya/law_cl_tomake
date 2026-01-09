import itertools
import logging

from src.utils.department_provider import get_department_names
from src.htmx_gen import gen_email_link
from src.string_management import URLS, TasksKey, AnnKey

# Load department list (will raise on JSON errors or missing file)
department_list = get_department_names()
id_em_elem_template = 'email_link_annid-{ann_idx}'
polling_wrapper = """<div id="result_table"
    hx-get="{STEP3_RESULT_STATUS}?{TASK_ID_KEY}={tasks_id}"
        hx-trigger="every 1s"
        hx-swap="innerHTML" hx-target="#main-container">
        {sub_detail}</div>
        """
no_polling_wrapper = """<div id="result_table" value="{tasks_id}">
        {sub_detail}</div>"""
def gen_result_table(table_container,tasks_id,ann_list):
    sub_detail = ''
    for clr,clr_anns in itertools.groupby(ann_list, key=lambda x: x['crawler']):
        clr_wrapper = """<div class="crawler-section">
        <details open><summary>{display_name} - {count} 筆資料</summary>
            {sub_table_text}</details>
        """
        sub_table_text = ''
        count = 0
        for ann in clr_anns:
            if ann.get(AnnKey.SELECTED.value) is False:
                continue
            
            inner_table = _gen_inner_table(tasks_id,ann)
            sub_table_text += inner_table
            count += 1
        if count == 0:
            continue
        sub_detail += clr_wrapper.format(display_name=clr.DISPLAY_NAME,count=count, sub_table_text=sub_table_text)
    if sub_detail == '':
        return 'loading...'
    return table_container.format(tasks_id=tasks_id, sub_detail=sub_detail,
                                STEP3_RESULT_STATUS=URLS.STEP3_RESULT_STATUS.value,
                                TASK_ID_KEY=TasksKey.TASK_ID.value)
def _gen_inner_table(tasks_id,ann):
    if ann.get(AnnKey.CONTENT.value) is None:
        return "<div class='waitingrror'>Announcement data is incomplete.</div>"
    if not ann_integrity_check(ann):
        # logging.error(f"Announcement integrity check failed for announcement: {ann}")
        return "<div class='error'>error</div>"
    ann_idx = ann.get(AnnKey.IDX.value,-1)
    ann_date = ann.get(AnnKey.DATE.value,'')
    ann_attachment_list = ann.get(AnnKey.ATTACHMENTS.value,[])
    ann_department_list = ann.get(AnnKey.DEPARTMENTS.value,[])
    ann_cc_department_list = ann.setdefault(AnnKey.CC_DEPARTMENTS.value,[])
    ann_title = ann.get(AnnKey.TITLE.value,'')
    ann_link = ann.get(AnnKey.LINK.value,'')
    ann_content = ann.get(AnnKey.CONTENT.value,'')
    full_content = f"{ann_content}\n\nLink: {ann_link}" if ann_link else ann_content
    email_elem = gen_email_link(ann_department_list,ann_title,full_content,ann_cc_department_list)

    subject_html = f'<a href="{ann_link}" target="_blank">{ann_title}</a>' if ann_link else ann_title
    attachment_html = ', '.join(ann_attachment_list) if ann_attachment_list else '無'

    return f"""
    <div class="table-container">
        <!-- 標題列 -->
        <div class="header-row">
            <div class="date-cell">{ann_date}</div>
            <div class="subject-cell">{subject_html}</div>
            <div class="attachment-cell">{attachment_html}</div>
        </div>
        
        <!-- 內容列 -->
        <div class="content-row">
            <div class="departments-cell">
                {_gen_checkbox_dept_options(tasks_id,ann_idx,ann_department_list,ann_cc_department_list)}
            </div>

        </div>
    </div>"""
            # <!-- 發送郵件列 -->
            # <div class="send-email-cell" id="{id_em_elem_template.format(ann_idx=ann_idx)}">
            #     {email_elem}
            # </div>

def _gen_checkbox_dept_options(task_id,ann_idx,dept_set,cc_set):
    patch_wrapper = """<form hx-patch="{STEP3_RESULT_DEPT_SELECT}?{TASK_ID_KEY}={task_id}" 
        hx-trigger="change"
        hx-target="#{id_em_elem}"
        hx-swap="innerHTML">{row_options}</form>
    """
    
    options_html = ""
    for dept_idx,dept_name in enumerate(department_list):
        to_checked = 'checked' if dept_name in dept_set else ''
        cc_checked = 'checked' if dept_name in cc_set else ''
        checked_attr = 'checked' if cc_checked or to_checked else ''
        option_html = f'''
        <div class="dept-option">
            <input type="checkbox" name="dept_option_{dept_idx}" 
                value="ann_idx:{ann_idx} dept_idx:{dept_idx} type:outter" {checked_attr}> 
            <label>{dept_name}</label>
            <div class="recipient-type" style="margin-left: 20px; {'display: inline-block;'}">
                <input type="radio" name="dept_type_{dept_idx}" id="to_{dept_idx}" 
                    value="ann_idx:{ann_idx} dept_idx:{dept_idx} type:to" {to_checked}>
                <label for="to_{dept_idx}">收件者</label>
                <input type="radio" name="dept_type_{dept_idx}" id="cc_{dept_idx}" 
                    value="ann_idx:{ann_idx} dept_idx:{dept_idx} type:cc" {cc_checked}>
                <label for="cc_{dept_idx}">副本</label>
            </div>
        </div>
        '''
        options_html += option_html
    return patch_wrapper.format(task_id=task_id,
                id_em_elem=id_em_elem_template.format(ann_idx=ann_idx), row_options=options_html,
                STEP3_RESULT_DEPT_SELECT=URLS.STEP3_RESULT_DEPT_SELECT.value,
                TASK_ID_KEY=TasksKey.TASK_ID.value)
                
def ann_integrity_check(ann):
    required_keys = [AnnKey.IDX.value, AnnKey.DATE.value, AnnKey.TITLE.value,
                     AnnKey.LINK.value, AnnKey.CONTENT.value,
                     AnnKey.ATTACHMENTS.value, AnnKey.SELECTED.value]
    for key in required_keys:
        if key not in ann:
            logging.error(f"Announcement missing required key: {key}")
            return False
    return True