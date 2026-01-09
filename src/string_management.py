from enum import StrEnum, auto
from typing import TypedDict, Optional, List, Any

class URLS(StrEnum):
    """Web server URL routes"""
    # Main routes
    _nginx_location = '/law-cl'
    ROOT = _nginx_location+"/"
    STATIC = _nginx_location+"/static"
    CSS = _nginx_location+"/static/my_css.css"
    JS = _nginx_location+"/static/main.js"
    # Step 1 - Initialize
    STEP1_INIT = _nginx_location+"/step1_init"
    STEP1_SET_ENABLE_CRAWLERS = _nginx_location+"/step1_set_enable_crawlers"
    
    # Step 2 - Announcement status
    STEP2_ANN_STATUS = _nginx_location+"/step2_ann_status"
    STEP2_ANN_STATUS_SELECTED_ONLY = _nginx_location+"/step2_ann_status_selected_only"
    STEP2_ANN_SELECT = _nginx_location+"/steps2_ann_select"
    STEP2_ANN_SELECT_BYDATE = _nginx_location+"/step2_ann_select_bydate"
    STEP2_TO_STEP3 = _nginx_location+"/step2_to_step3"
    
    # Step 3 - Result status
    STEP3_RESULT_STATUS = _nginx_location+"/step3_result_status"
    STEP3_RESULT_DEPT_SELECT = _nginx_location+"/step3_result_dept_select"
    
    # Step 4 - Database save
    STEP4_RESULT_STATUS = _nginx_location+"/step4_result_status"
    SAVE_TO_DB = _nginx_location+"/save_to_db"
    
    # Database lookup
    LOOKUP_DB = _nginx_location+"/lookup_db"
    
    # Approval
    APPROVAL_PAGE = _nginx_location+"/approval_page"
    APPROVAL_LIST = _nginx_location+"/approval_list"
    APPROVAL_DETAIL = _nginx_location+"/approval_detail"
    APPROVAL_ACTION = _nginx_location+"/approval_action"
    APPROVAL_PATCH_DEPT = _nginx_location+"/approval_patch_dept"

    # Execution
    EXECUTION_PAGE = _nginx_location+"/execution_page"
    EXECUTION_LIST = _nginx_location+"/execution_list"
    EXECUTION_ACTION = _nginx_location+"/execution_action"

    # Knowledge
    KNOWLEDGE_PAGE = _nginx_location+"/knowledge_page"
    KNOWLEDGE_LIST = _nginx_location+"/knowledge_list"
    KNOWLEDGE_CONTENT = _nginx_location+"/knowledge_content"
    KNOWLEDGE_SAVE = _nginx_location+"/knowledge_save"

    # Utilities
    HEARTBEAT = _nginx_location+"/heartbeat"
    SERVER_STATUS = _nginx_location+"/server_status"
    ANN_CHECKBOX_SET = _nginx_location+"/ann_checkbox_set"

class AnnKey(StrEnum):
    """Announcement dictionary keys"""
    SELECTED = "selected"
    CRAWLER = "crawler"
    IDX = "idx"
    DATE = "date"
    TITLE = "title"
    LINK = "link"
    CONTENT = "content"
    ATTACHMENTS = "attachments"
    DEPARTMENTS = "departments"
    CC_DEPARTMENTS = "cc_departments"
    LOOKED = "looked"
    SENDED = "sended"

class Announcement(TypedDict):
    """Announcement dictionary structure"""
    selected: Optional[bool]
    crawler: Optional[Any] # Crawler instance
    idx: Optional[int]
    date: Optional[str]
    title: Optional[str]
    link: Optional[str]
    content: Optional[str]
    attachments: Optional[List[str]]
    departments: Optional[List[str]]
    cc_departments: Optional[List[str]]
    looked: Optional[bool]
    sended: Optional[bool]

class TasksKey(StrEnum):
    """Task dictionary keys"""
    TASK_ID = "task_id"
    STATUS = "status"
    ANNOUNCEMENTS = "announcements"
    LOADING = "loading"

class TaskStatus(StrEnum):
    """Task status values"""
    CRAWLING = "Crawling"
    SELECTING = "Selecting"
    STEP3_PROCESSING = "Step3 Processing"
    STEP3_COMPLETED = "Step3 Completed"
    UNKNOWN = "unknown"