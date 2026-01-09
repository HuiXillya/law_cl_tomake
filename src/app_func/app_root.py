import configparser
from src.htmx_gen import gen_htmx_root
from src.string_management import URLS, TasksKey
config = configparser.ConfigParser()
config.read('config.ini')

def old_root():
    with open(config['HTML']['front_path'], 'r', encoding='utf-8') as f:
        html_content = f.read()
    # Replace placeholders with centralized constants for routes & task keys
    formatted = html_content.format(
        STEP1_INIT=URLS.STEP1_INIT.value,
        STEP2_ANN_STATUS=URLS.STEP2_ANN_STATUS.value,
        STEP3_RESULT_STATUS=URLS.STEP3_RESULT_STATUS.value,
        STEP4_RESULT_STATUS=URLS.STEP4_RESULT_STATUS.value,
        LOOKUP_DB=URLS.LOOKUP_DB.value,
        STEP1_SET_ENABLE_CRAWLERS=URLS.STEP1_SET_ENABLE_CRAWLERS.value,
        TASK_ID_KEY=TasksKey.TASK_ID.value
    )
    return formatted

def root(task_id='none', step='step1'):
    return gen_htmx_root(task_id=task_id, step=step)

