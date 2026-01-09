import itertools
from src.string_management import URLS, TasksKey, AnnKey
def gen_checkbox_table(task_id,anns :list,seleted_only: bool=False):
    table_text = ''
    if len(anns) == 0:
        return table_text
    if AnnKey.IDX.value not in anns[0]:
        _ = _set_anns_id(anns) 
    # htmx_checkbox_trigger

        
    for cl,cln_anns in itertools.groupby(anns, key=lambda x: x['crawler']):
        sub_table_text = ''
        ann_count = 0
        for ann in cln_anns:
            ann_count += 1
            idx = ann[AnnKey.IDX.value]
            _ = _input_ann_checker(ann)
            date_elem = f"<a>{ann.get(AnnKey.DATE.value)}</a>"
            linked_title_elem = f'<a href="{ann.get(AnnKey.LINK.value)}" target="_blank">{ann.get(AnnKey.TITLE.value)}</a>'
            if ann.setdefault(AnnKey.SELECTED.value,False) :
                checked_str = f'<input name=id-{idx} id=annid-{idx} type=checkbox checked>'
                sub_table_text +=(f"<li>{checked_str}&nbsp;{date_elem}&nbsp;{linked_title_elem}</li>")
            elif not seleted_only:
                checked_str = f'<input name=id-{idx} id=annid-{idx} type=checkbox >'
                sub_table_text +=(f"<li>{checked_str}&nbsp;{date_elem}&nbsp;{linked_title_elem}</li>")
        detail_start = f'<details open><summary>{cl.DISPLAY_NAME} - {ann_count} 筆資料</summary>'
        detail_end = '</details>'
        table_text += detail_start + f'<ul>{sub_table_text}</ul>' + detail_end
    return check_form_container.format(dates_options_str = _gen_date_options(anns),
                                        task_id=task_id, inner_input=table_text,
                                        STEP2_ANN_SELECT_BYDATE=URLS.STEP2_ANN_SELECT_BYDATE.value,
                                        STEP2_ANN_STATUS_SELECTED_ONLY=URLS.STEP2_ANN_STATUS_SELECTED_ONLY.value,
                                        STEP2_ANN_STATUS=URLS.STEP2_ANN_STATUS.value,
                                        STEP2_TO_STEP3=URLS.STEP2_TO_STEP3.value,
                                        STEP2_ANN_SELECT=URLS.STEP2_ANN_SELECT.value,
                                        TASK_ID_KEY=TasksKey.TASK_ID.value)

def gen_no_checkbox_table(task_id,anns :list,polling: bool=True,seleted_only: bool=False):
    table_container = """<div id="ann_table_poller"
        hx-get="{STEP2_ANN_STATUS}?{TASK_ID_KEY}={task_id}"
        hx-trigger="every 1s"
        hx-swap="innerHTML" hx-target="#main-container"> now loading...
        {table_text}</div>
        """
    if polling == False:
        table_container = """<div id="ann_table_static">
        {table_text}</div>
        """
    table_text = ''
    for cl,cln_anns in itertools.groupby(anns, key=lambda x: x['crawler']):
        sub_table_text = ''
        ann_count = 0
        for ann in cln_anns:
            _ = _input_ann_checker(ann)
            if not seleted_only or ann.get(AnnKey.SELECTED.value,True): 
                date_elem = f"<a>{ann.get(AnnKey.DATE.value)}</a>"
                linked_title_elem = f'<a href="{ann.get(AnnKey.LINK.value)}" target="_blank">{ann.get(AnnKey.TITLE.value)}</a>'
                sub_table_text += f"<li>{date_elem}&nbsp;{linked_title_elem}</li>"
            ann_count += 1
        detail_start = f'<details open><summary>{cl.DISPLAY_NAME} - {ann_count} 筆資料</summary>'
        detail_end = '</details>'
        table_text += detail_start + f'<ul>{sub_table_text}</ul>' + detail_end
    return table_container.format(task_id=task_id, table_text=table_text,
                                  STEP2_ANN_STATUS=URLS.STEP2_ANN_STATUS.value,
                                  TASK_ID_KEY=TasksKey.TASK_ID.value)
def _input_ann_checker(ann :dict) -> bool:
    try:# assert isinstance(ann, dict)
        assert AnnKey.DATE.value in ann
        assert AnnKey.TITLE.value in ann
        assert AnnKey.LINK.value in ann
    except:
        raise ValueError("Each announcement must be a dict with keys: 'date', 'title', 'link'")
    return True
def _set_anns_id(anns: list) -> bool:
    for idx, ann in enumerate(anns):
        ann[AnnKey.IDX.value] = idx 
    return True
def _gen_date_options(announcements: list) -> str:
    return "".join([f'<option value="{my_date}">{my_date}</option>'
                                 for my_date in sorted(set(ann[AnnKey.DATE.value] for ann in announcements), reverse=True)])
check_form_container = """
    <div id="form_container">
    <div class="top nav">
        <div id="selected-dates" >
            <label for="date-select">選擇日期:</label>
                <select name="select_date" id="dateselect" >
                    {dates_options_str}
                </select>
            <button type="submit" hx-post="{STEP2_ANN_SELECT_BYDATE}?{TASK_ID_KEY}={task_id}" 
            hx-trigger="click" hx-include="[name^='select']"  
            hx-target="#main-container" hx-swap="innerHTML"
            >選擇日期</button>
        </div>
            <button type="show_selected" 
            hx-get="{STEP2_ANN_STATUS_SELECTED_ONLY}?{TASK_ID_KEY}={task_id}" 
            hx-trigger="click"
            hx-target="#main-container" hx-swap="innerHTML"
            >顯示已選取項目</button>
        <button type="show_all"
            hx-get="{STEP2_ANN_STATUS}?{TASK_ID_KEY}={task_id}" 
            hx-trigger="click"
            hx-target="#main-container" hx-swap="innerHTML"
            >顯示全部項目</button>
        <button type="submit"
            hx-post="{STEP2_TO_STEP3}?{TASK_ID_KEY}={task_id}"
            hx-trigger="click"
            hx-target="#main-container" hx-swap="none"
        >送出選取</button>
    </div>
    <form hx-patch="{STEP2_ANN_SELECT}?{TASK_ID_KEY}={task_id}" 
        hx-trigger="change " 
        hx-swap="none">
        {inner_input}</form></div>"""