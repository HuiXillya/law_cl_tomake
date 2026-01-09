from src.string_management import URLS

def gen_knowledge_page():
    return f'''
    <div style="display: flex; height: 80vh; gap: 20px;">
        <div style="width: 30%; border-right: 1px solid #ccc; overflow-y: auto; padding-right: 10px;"
             hx-get="{URLS.KNOWLEDGE_LIST}" 
             hx-trigger="load">
             Loading departments...
        </div>
        <div id="knowledge-editor-container" style="width: 70%; padding-left: 10px;">
            <p>Select a department to edit its description.</p>
        </div>
    </div>
    '''

def gen_department_list(departments):
    """
    departments: list of dicts like {'deptname': '...', ...}
    """
    html = '<ul style="list-style: none; padding: 0;">'
    for dept in departments:
        name = dept.get('deptname')
        html += f'''
        <li style="padding: 5px; cursor: pointer; border-bottom: 1px solid #eee;"
            hx-get="{URLS.KNOWLEDGE_CONTENT}?dept_name={name}"
            hx-target="#knowledge-editor-container"
            onmouseover="this.style.backgroundColor='#f0f0f0'"
            onmouseout="this.style.backgroundColor='transparent'">
            {name}
        </li>
        '''
    html += '</ul>'
    return html

def gen_editor(dept_name, content):
    return f'''
    <h3>Editing: {dept_name}</h3>
    <form hx-post="{URLS.KNOWLEDGE_SAVE}?dept_name={dept_name}" hx-swap="none">
        <textarea name="content" style="width: 100%; height: 60vh; font-family: monospace; padding: 10px;">{content}</textarea>
        <br><br>
        <button type="submit" style="padding: 10px 20px; cursor: pointer;">Save Changes</button>
        <span id="save-status"></span>
    </form>
    <script>
        document.body.addEventListener('htmx:afterRequest', function(evt) {{
            if(evt.detail.elt.tagName === 'FORM') {{
                const status = evt.detail.elt.querySelector('#save-status');
                if (evt.detail.successful) {{
                    status.textContent = 'Saved!';
                    status.style.color = 'green';
                    setTimeout(() => status.textContent = '', 3000);
                }} else {{
                    status.textContent = 'Error saving.';
                    status.style.color = 'red';
                }}
            }}
        }});
    </script>
    '''
