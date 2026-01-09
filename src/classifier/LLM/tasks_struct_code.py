from typing import TypedDict, Optional
from enum import StrEnum, auto
from time import time
# 1. 集中管理 Key 的名稱
class TaskKeys(StrEnum):
    STATUS = auto()      # 自動變成 "user_id"
    QUESTION = auto() # 自動變成 "is_logged_in"
    ANSWER = auto()  # 自動變成 "last_action"
    LAST_UPDATED = auto()  
    # 也可以手動指定
    # API_TOKEN = "api_access_token"
class TasksDict(TypedDict):
    status: str
    question: str
    answer: Optional[str]
    last_updated: float
class StatusCode(StrEnum):
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

def __self_check():
    """ A simple self-check function to verify the structure """
    sample_task: TasksDict = {
        TaskKeys.STATUS: StatusCode.RECEIVED,
        TaskKeys.QUESTION: "Is the system working?",
        TaskKeys.ANSWER: None,
        TaskKeys.LAST_UPDATED: time()
    }
    assert isinstance(sample_task, dict)
    return True
# Run self-check
__self_check()