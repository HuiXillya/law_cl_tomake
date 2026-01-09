import time
import os 
import shutil
import logging
import configparser
import asyncio

logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('config.ini')
default_interval = config.getint('Heartbeat', 'INTERVAL', fallback=300)
default_timeout = config.getint('Heartbeat', 'TIMEOUT', fallback=600)
def update_time(task_id: str,tasks: dict):

    if task_id in tasks:
        tasks[task_id]["last_beat"] = time.time()
        return {"status":"success","message":"Heartbeat received"+time.ctime(tasks[task_id]["last_beat"])}
    else:
        return {"status":"error","message":"Task ID not found"}
async def loop_maintain_tasks(tasks: dict, interval: int = default_interval, timeout: int = 600):
    while True:
        _maintain_tasks(tasks, timeout)
        await asyncio.sleep(interval)
def _maintain_tasks(tasks: dict, timeout: int = default_timeout):
    config = configparser.ConfigParser()
    config.read('config.ini')
    output_base_path = config.get('Outputdir', 'OUTPUT_PATH', fallback='./output')
    current_time = time.time()
    to_remove = []
    for task_id, task_info in tasks.items():
        if current_time - task_info.setdefault("last_beat", time.time()) > timeout:
            logger.info(f"Removing stale task: {task_id}")
            to_remove.append(task_id)
    for task_id in to_remove:
        del tasks[task_id]
    #list dirs in output_base_path
    
    to_remove = set(os.listdir(output_base_path)) - set(tasks.keys())
    for dir_name in to_remove:
        dir_path = os.path.join(output_base_path, dir_name)
        if os.path.isdir(dir_path):
            try:
                # Remove directory and its contents
                shutil.rmtree(dir_path)
                logger.info(f"Removed stale output directory: {dir_path}")
            except Exception as e:
                logger.error(f"Error removing directory {dir_path}: {e}")

        
        