
from src.string_management import URLS, TasksKey
import configparser

def gen_htmx_root(task_id,step):
    config = configparser.ConfigParser()
    config.read('config.ini')
    llm_enabled = config.getint('LLM', 'llm_classifier', fallback=0) == 1

    knowledge_btn = ""
    if llm_enabled:
        knowledge_btn = '''
            <button id="knowledge_page"
                hx-get="{KNOWLEDGE_PAGE}" hx-target="#main-container"
                hx-trigger="click" hx-swap="innerHTML" hx-replace-url="{ROOT_URL}?step=knowledge">
                (new)知識庫</button>
        '''.format(KNOWLEDGE_PAGE=URLS.KNOWLEDGE_PAGE.value, ROOT_URL=URLS.ROOT.value)

    if not task_id:
        task_id = "none"
    if step == "step1":
        main_content = init_load.format(
            STEP1_INIT=URLS.STEP1_INIT.value
        )
    elif step == "step2":
        main_content = step2_load.format(
            task_id=task_id,
            STEP2_ANN_STATUS=URLS.STEP2_ANN_STATUS.value,
            ROOT_URL=URLS.ROOT.value,
            TASK_ID_KEY=TasksKey.TASK_ID.value
        )
    elif step == "step3":
        main_content = step3_load.format(
            task_id=task_id,
            STEP3_RESULT_STATUS=URLS.STEP3_RESULT_STATUS.value,
            ROOT_URL=URLS.ROOT.value,
            TASK_ID_KEY=TasksKey.TASK_ID.value
        )
    elif step == "step4":
        main_content = step4_load.format(
            task_id=task_id,
            STEP4_RESULT_STATUS=URLS.STEP4_RESULT_STATUS.value,
            ROOT_URL=URLS.ROOT.value,
            TASK_ID_KEY=TasksKey.TASK_ID.value
        )
    elif step == "lookup_db":
        main_content = lookup_db_load.format(
            LOOKUP_DB=URLS.LOOKUP_DB.value,
            ROOT_URL=URLS.ROOT.value)
    elif step == "approval":
        main_content = approval_load.format(
            APPROVAL_LIST=URLS.APPROVAL_LIST.value,
            ROOT_URL=URLS.ROOT.value
        )
    elif step == "execution":
        main_content = execution_load.format(
            EXECUTION_LIST=URLS.EXECUTION_LIST.value,
            ROOT_URL=URLS.ROOT.value
        )
    elif step == "knowledge":
        main_content = knowledge_load.format(
            KNOWLEDGE_PAGE=URLS.KNOWLEDGE_PAGE.value,
            ROOT_URL=URLS.ROOT.value
        )
    else:
        main_content = init_load.format(
            STEP1_INIT=URLS.STEP1_INIT.value
        )
    return template.format(task_id=task_id, main_content=main_content,
                           HEARTBEAT=URLS.HEARTBEAT.value,
                           STEP1_INIT=URLS.STEP1_INIT.value,
                           STEP2_ANN_STATUS=URLS.STEP2_ANN_STATUS.value,
                           STEP3_RESULT_STATUS=URLS.STEP3_RESULT_STATUS.value,
                           STEP4_RESULT_STATUS=URLS.STEP4_RESULT_STATUS.value,
                           LOOKUP_DB=URLS.LOOKUP_DB.value,
                           APPROVAL_LIST=URLS.APPROVAL_LIST.value,
                           EXECUTION_LIST=URLS.EXECUTION_LIST.value,
                           KNOWLEDGE_PAGE=URLS.KNOWLEDGE_PAGE.value,
                           KNOWLEDGE_BUTTON=knowledge_btn,
                           TASK_ID_KEY=TasksKey.TASK_ID.value,
                           CSS=URLS.CSS.value,
                           JS=URLS.JS.value,
                           ROOT_URL=URLS.ROOT.value)

template = '''
<html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.8/dist/htmx.min.js" 
            integrity="sha384-/TgkGk7p307TH7EXJDuUlgG3Ce1UVolAOFopFekQkkXihi5u/6OCvVKyz1W+idaz" 
            crossorigin="anonymous"></script>
        <link rel="stylesheet" href="{CSS}">
    </head>
    <body data-root-url="{ROOT_URL}">
        <div id="global-vars" style="display: none;">
            <input type="hidden" id="current-task-id" name="{TASK_ID_KEY}" value="{task_id}">
        </div>
        <div id="heart" style="display: none;"
        hx-get="{HEARTBEAT}"
            hx-trigger="every 150s"
            hx-swap="none"
            hx-include="#global-vars"
            >
        </div>
        <div id="top_nav">
            <button id="step1" 
                hx-get="{STEP1_INIT}" hx-target="#main-container"
                hx-trigger="click" hx-swap="innerHTML" hx-replace-url="{ROOT_URL}?step=step1">
                步驟 1: 初始化</button>
            <button id="step2" 
                hx-get="{STEP2_ANN_STATUS}" hx-target="#main-container"
                hx-trigger="click" hx-swap="innerHTML" hx-include="#current-task-id" hx-replace-url="{ROOT_URL}?step=step2&{TASK_ID_KEY}={task_id}">
                步驟 2: 選擇條目</button>

            <button id="step3"
                hx-get="{STEP3_RESULT_STATUS}" hx-target="#main-container"
                hx-trigger="click" hx-swap="innerHTML" hx-include="#current-task-id"  hx-replace-url="{ROOT_URL}?step=step3&{TASK_ID_KEY}={task_id}">
                步驟 3: 判斷結果</button>

            <button id="step4" 
                hx-get="{STEP4_RESULT_STATUS}" hx-target="#main-container"
                hx-trigger="click" hx-swap="innerHTML" hx-include="#current-task-id"  hx-replace-url="{ROOT_URL}?step=step4&{TASK_ID_KEY}={task_id}">
                步驟 4: 產出簽核</button>

            <button id="db_lookup" 
                hx-get="{LOOKUP_DB}" hx-target="#main-container"
                hx-trigger="click" hx-swap="innerHTML" hx-replace-url="{ROOT_URL}?step=lookup_db">
                檢索資料庫</button>

            <button id="approval_page" 
                hx-get="{APPROVAL_LIST}" hx-target="#main-container"
                hx-trigger="click" hx-swap="innerHTML" hx-replace-url="{ROOT_URL}?step=approval">
                主管簽核</button>

            <button id="execution_page" 
                hx-get="{EXECUTION_LIST}" hx-target="#main-container"
                hx-trigger="click" hx-swap="innerHTML" hx-replace-url="{ROOT_URL}?step=execution">
                執行寄信</button>
            {KNOWLEDGE_BUTTON}
        </div>
        <div id="main-container">
            {main_content}
        </div>
        <script src="{JS}"></script>
    </body>
</html>
'''
init_load = '''
        <div hx-get="{STEP1_INIT}" hx-trigger="load" hx-swap="innerHTML">
        </div>'''
step2_load = '''
    <div hx-get="{STEP2_ANN_STATUS}" hx-trigger="load" hx-swap="innerHTML"
            hx-include="#current-task-id" hx-replace-url="{ROOT_URL}?{TASK_ID_KEY}={task_id}&step=step2">
        </div>'''
step3_load = '''
    <div hx-get="{STEP3_RESULT_STATUS}" hx-trigger="load" hx-swap="innerHTML"
            hx-include="#current-task-id" hx-replace-url="{ROOT_URL}?{TASK_ID_KEY}={task_id}&step=step3">
        </div>'''
step4_load = '''
    <div hx-get="{STEP4_RESULT_STATUS}" hx-trigger="load" hx-swap="innerHTML"
            hx-include="#current-task-id" hx-replace-url="{ROOT_URL}?{TASK_ID_KEY}={task_id}&step=step4">
        </div>'''
lookup_db_load =  '''
    <div hx-get="{LOOKUP_DB}" hx-trigger="load" hx-swap="innerHTML"
            hx-include="#current-task-id" hx-replace-url="{ROOT_URL}?step=lookup_db">
        </div>'''
approval_load = '''
    <div hx-get="{APPROVAL_LIST}" hx-trigger="load" hx-swap="innerHTML"
            hx-replace-url="{ROOT_URL}?step=approval">
        </div>'''
execution_load = '''
    <div hx-get="{EXECUTION_LIST}" hx-trigger="load" hx-swap="innerHTML"
            hx-replace-url="{ROOT_URL}?step=execution">
        </div>'''
knowledge_load = '''
    <div hx-get="{KNOWLEDGE_PAGE}" hx-trigger="load" hx-swap="innerHTML"
            hx-replace-url="{ROOT_URL}?step=knowledge">
        </div>'''
# JavaScript logic moved to static/main.js
