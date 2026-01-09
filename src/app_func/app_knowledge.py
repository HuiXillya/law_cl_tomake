from pathlib import Path
from fastapi.responses import HTMLResponse, PlainTextResponse
from src.htmx_gen.gen_knowledge import gen_knowledge_page, gen_department_list, gen_editor
from src.utils.department_provider import get_departments, _departments_path

def get_knowledge_desc_dir() -> Path:
    return _departments_path().parent / "Dept_description"

async def knowledge_page_endpoint():
    return HTMLResponse(gen_knowledge_page())

async def knowledge_list_endpoint():
    depts = get_departments()
    return HTMLResponse(gen_department_list(depts))

async def knowledge_content_endpoint(dept_name: str):
    # Security check: ensure dept_name is valid
    valid_depts = [d['deptname'] for d in get_departments()]
    if dept_name not in valid_depts:
        return HTMLResponse("Invalid department", status_code=400)
    
    file_path = get_knowledge_desc_dir() / f"{dept_name}.md"
    content = ""
    if file_path.exists():
        content = file_path.read_text(encoding='utf-8')
    else:
        content = f"# {dept_name}\n\nNo description yet."
        
    return HTMLResponse(gen_editor(dept_name, content))

async def knowledge_save_endpoint(dept_name: str, request_form: dict):
    # Security check
    valid_depts = [d['deptname'] for d in get_departments()]
    if dept_name not in valid_depts:
        return PlainTextResponse("Invalid department", status_code=400)
    
    content = request_form.get('content')
    if content is None:
        return PlainTextResponse("No content provided", status_code=400)
        
    file_path = get_knowledge_desc_dir() / f"{dept_name}.md"
    try:
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        return PlainTextResponse("Saved successfully")
    except Exception as e:
        return PlainTextResponse(f"Error saving: {e}", status_code=500)
