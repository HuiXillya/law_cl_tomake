from fastapi import FastAPI,Request,BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, PlainTextResponse
from contextlib import asynccontextmanager
import asyncio
import time
import uuid
import uvicorn
import os
import logging
import configparser
from urllib.parse import unquote
from src.app_func import (
    init_db,check_connection,
    root,step1_init,step1_start,step2_status,step2_start,
    set_selected_announcements,set_selected_announcements_bydate,
    step3_result,
    patch_department_select,
    step4_result_status,save_to_db,
    lookup_db,
    update_time,loop_maintain_tasks,
    ann_checkbox_set,
    app_approval,
    app_execution,
    app_knowledge
)
from src.string_management import URLS, TasksKey
from src.logging_config import setup_logging
from src.utils.mount_check import verify_departments_from_config

# Initialize logging
setup_logging()

my_tasks = {}

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動前檢查：確認 config.ini, department JSON 及各 department 的 md 檔
    verify_departments_from_config(logger=logger)

    # 啟動背景任務並記錄，確保 shutdown 時能取消
    task = asyncio.create_task(loop_maintain_tasks(my_tasks))
    app.state.bg_task = task
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

app = FastAPI(lifespan = lifespan)

# main web page route return HTLM response
@app.get(URLS.ROOT.value,response_class=HTMLResponse)
async def api_root(task_id: str = 'none',step: str = 'step1'):
    return HTMLResponse(content=root(task_id,step), status_code=200)
@app.get(URLS.CSS.value,response_class=FileResponse)
async def api_css():
    return FileResponse("static/default.css", media_type="text/css")
@app.get(URLS.JS.value,response_class=FileResponse)
async def api_js():
    return FileResponse("static/main.js", media_type="application/javascript")
@app.get(URLS.STEP1_INIT.value,response_class=HTMLResponse)
async def api_step1_init():
    # return current server status and witch crawler would start
    return HTMLResponse(content=step1_init(), status_code=200)
@app.post(URLS.STEP1_SET_ENABLE_CRAWLERS.value,response_class=JSONResponse)
async def api_step1_start(request: Request, background_tasks: BackgroundTasks):
    task_id = await step1_start(request,background_tasks, tasks=my_tasks)
    return JSONResponse(content= {TasksKey.TASK_ID.value: task_id}, status_code=202)
@app.get(URLS.STEP2_ANN_STATUS.value,response_class=HTMLResponse)
async def api_step2_status(task_id: str):
    return HTMLResponse(content=step2_status(task_id,my_tasks), status_code=200)
@app.get(URLS.STEP2_ANN_STATUS_SELECTED_ONLY.value)
async def api_step2_status_selected_only(task_id: str):
    return HTMLResponse(content=step2_status(task_id,my_tasks, display_selected_only=True), status_code=200)
@app.patch(URLS.STEP2_ANN_SELECT.value,response_class=JSONResponse)
async def step2_select(request: Request,task_id: str):
    # receive selected announcement list
    _ = await set_selected_announcements(request,task_id,my_tasks)
    return JSONResponse(content= {TasksKey.TASK_ID.value: task_id}, status_code=200)
@app.post(URLS.STEP2_ANN_SELECT_BYDATE.value,response_class=HTMLResponse)
async def api_step2_select_bydate(request: Request,task_id: str):
    # receive date filter for announcement selection
    data = await request.form()
    logger.debug(f"Received form data for date selection: {data}")
    _ = await set_selected_announcements_bydate(request,task_id,my_tasks)
    return HTMLResponse(content=step2_status(task_id,my_tasks), status_code=200)
@app.post(URLS.STEP2_TO_STEP3.value,response_class=JSONResponse)
async def api_step2_to_step3(task_id: str,background_tasks: BackgroundTasks):
    # start downloading selected announcements
    rtm = await step2_start(background_tasks,task_id,my_tasks)
    rtm.update({TasksKey.TASK_ID.value: task_id})
    return JSONResponse(content= rtm, status_code=202)
@app.get(URLS.STEP3_RESULT_STATUS.value,response_class=HTMLResponse)
async def step3_status(task_id: str):
    # return current status of the downloading task
    return HTMLResponse(content=step3_result(task_id,my_tasks), status_code=200)
@app.patch(URLS.STEP3_RESULT_DEPT_SELECT.value,response_class=HTMLResponse)
async def api_step3_select(request: Request,task_id: str=None):
    # receive selected department list
    content = await patch_department_select(request,task_id,my_tasks)
    return HTMLResponse(content=content, status_code=200)
@app.get(URLS.STEP4_RESULT_STATUS.value,response_class=HTMLResponse)
async def api_step4_result_status(task_id: str):
    # return current status of the final task
    return HTMLResponse(content=step4_result_status(task_id,my_tasks), status_code=200)
@app.get(URLS.SAVE_TO_DB.value,response_class=HTMLResponse)
async def api_step4_save_to_db(task_id: str):
    # save an ann result to db
    return HTMLResponse(content=save_to_db(task_id,my_tasks), status_code=200)
@app.get(URLS.LOOKUP_DB.value,response_class=HTMLResponse)
async def api_lookup_db():
    return HTMLResponse(content=lookup_db(), status_code=200)

@app.patch(URLS.ANN_CHECKBOX_SET.value,response_class=JSONResponse)
async def api_ann_checkbox_set(task_id:str,ann_idx :str,checkbox_name :str):
    res = ann_checkbox_set(task_id,my_tasks,ann_idx,checkbox_name)
    return {"status": "success"}
#other functions
@app.get(URLS.HEARTBEAT.value)
async def heartbeat(task_id: str):
    res = update_time(task_id, my_tasks)
    return res 

@app.get(URLS.SERVER_STATUS.value)
async def server_status():
    return {"status": "running"}


@app.get(URLS.APPROVAL_LIST.value, response_class=HTMLResponse)
async def api_approval_list():
    return HTMLResponse(content=app_approval.approval_list(), status_code=200)

@app.get(URLS.APPROVAL_DETAIL.value, response_class=HTMLResponse)
async def api_approval_detail(task_id: str):
    return HTMLResponse(content=app_approval.approval_detail(task_id), status_code=200)

@app.post(URLS.APPROVAL_ACTION.value, response_class=HTMLResponse)
async def api_approval_action(request: Request):
    return HTMLResponse(content=await app_approval.approval_action(request), status_code=200)

@app.patch(URLS.APPROVAL_PATCH_DEPT.value, response_class=HTMLResponse)
async def api_approval_patch_dept(request: Request):
    return HTMLResponse(content=await app_approval.approval_patch_dept(request), status_code=200)

@app.get(URLS.EXECUTION_LIST.value, response_class=HTMLResponse)
async def api_execution_list():
    return HTMLResponse(content=app_execution.execution_list(), status_code=200)

@app.api_route(URLS.EXECUTION_ACTION.value, methods=["GET", "POST"], response_class=HTMLResponse)
async def api_execution_action(request: Request):
    return HTMLResponse(content=await app_execution.execution_action(request), status_code=200)

@app.get(URLS.KNOWLEDGE_PAGE.value, response_class=HTMLResponse)
async def api_knowledge_page():
    config = configparser.ConfigParser()
    config.read('config.ini')
    if config.getint('LLM', 'llm_classifier', fallback=0) != 1:
        return HTMLResponse("Feature disabled", status_code=403)
    return await app_knowledge.knowledge_page_endpoint()

@app.get(URLS.KNOWLEDGE_LIST.value, response_class=HTMLResponse)
async def api_knowledge_list():
    config = configparser.ConfigParser()
    config.read('config.ini')
    if config.getint('LLM', 'llm_classifier', fallback=0) != 1:
        return HTMLResponse("Feature disabled", status_code=403)
    return await app_knowledge.knowledge_list_endpoint()

@app.get(URLS.KNOWLEDGE_CONTENT.value, response_class=HTMLResponse)
async def api_knowledge_content(dept_name: str):
    config = configparser.ConfigParser()
    config.read('config.ini')
    if config.getint('LLM', 'llm_classifier', fallback=0) != 1:
        return HTMLResponse("Feature disabled", status_code=403)
    return await app_knowledge.knowledge_content_endpoint(dept_name)

@app.post(URLS.KNOWLEDGE_SAVE.value, response_class=PlainTextResponse)
async def api_knowledge_save(dept_name: str, request: Request):
    config = configparser.ConfigParser()
    config.read('config.ini')
    if config.getint('LLM', 'llm_classifier', fallback=0) != 1:
        return PlainTextResponse("Feature disabled", status_code=403)
    form = await request.form()
    return await app_knowledge.knowledge_save_endpoint(dept_name, form)

if __name__ == "__main__":
    # 啟動前再次檢查（在直接以 python 啟動時適用）
    verify_departments_from_config(logger=logger)

    init_db()
    if check_connection() == False:
        logger.error("Database connection failed. Please check your database settings.")
        os._exit(1)
        
    uvicorn.run(app, host="0.0.0.0", port=8000,log_level='error')
