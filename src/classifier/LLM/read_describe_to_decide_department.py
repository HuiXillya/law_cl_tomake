import asyncio
import configparser
import json
import os
import random
import httpx
from src.classifier.LLM.langchain_compoment import predictPrompt

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
gbl_department_description_dict = {}
gbl_department_names =  []

# concurrency and retry settings (configurable via config.ini under GEMINI section)
MAX_CONCURRENT = config.getint('GEMINI', 'max_concurrent', fallback=3)
_semaphore = asyncio.Semaphore(MAX_CONCURRENT)

async def _check_if_this_department(ann_text: str, department_description: str) -> bool:
    """Call the LLM with limited concurrency and retry on 429 responses.

    Returns a boolean-like value (the parsed output) or False on non-retriable errors.
    """
    max_retries = config.getint('GEMINI', 'max_retries', fallback=4)
    base_delay = float(config.get('GEMINI', 'base_delay', fallback='1.0'))

    async with _semaphore:
        for attempt in range(1, max_retries + 1):
            try:
                resut = await predictPrompt.ainvoke({'ann_text': ann_text, 'department_descriptions': department_description})
                return resut
            except Exception as e:
                status_code = None
                if hasattr(e, 'response') and getattr(e.response, 'status_code', None):
                    status_code = e.response.status_code
                # httpx specific
                if isinstance(e, httpx.HTTPStatusError) and e.response is not None:
                    status_code = e.response.status_code

                # If rate limited (429) -> backoff and retry
                if status_code == 429 or '429' in str(e):
                    if attempt == max_retries:
                        # exhausted retries
                        return False
                    # exponential backoff with jitter
                    delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                    await asyncio.sleep(delay)
                    continue
                # For other errors, don't retry here — return False so caller can decide
                return False

def _init_describe_data():
    global gbl_department_description_dict
    global gbl_department_names
    
    # Read paths from config
    dept_json_path = config.get('DEPARTMENT', 'department_json')
    dir_path = config.get('DEPARTMENT', 'department_description')
    
    # Load department names from JSON
    if os.path.exists(dept_json_path):
        with open(dept_json_path, 'r', encoding='utf-8') as f:
            dept_data = json.load(f)
            gbl_department_names = [item['deptname'] for item in dept_data]
    else:
        print(f"Warning: Department JSON file not found at {dept_json_path}")
        gbl_department_names = []

    # Load descriptions
    for department_name in gbl_department_names:
        description = _load_department_description(department_name, dir_path)
        gbl_department_description_dict[department_name] = description
    return True
def _load_department_description(department_name: str,dir_path: str) -> str:
    file_path = f"{dir_path}/{department_name}.md"
    with open(file_path, mode='r', encoding='utf-8') as f:
        content = f.read()
    return content
async def read_describe_to_decide_department(ann_text: str) -> dict[str, bool]:
    global gbl_department_description_dict
    global gbl_department_names
    if len(gbl_department_names) == 0 or len(gbl_department_description_dict) == 0:
        _ = _init_describe_data()
    results = await asyncio.gather(*[
        _check_if_this_department(ann_text, gbl_department_description_dict.get(department_name, ""))
        for department_name in gbl_department_names
    ])
    # Map department names to boolean results, preserving order
    return {name: bool(res) for name, res in zip(gbl_department_names, results)}