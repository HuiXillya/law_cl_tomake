from urllib.parse import quote
import logging
from src.utils.department_provider import get_department_email

logger = logging.getLogger(__name__)

def _get_email_address(departments) -> list:
    """Return list of email addresses for given department names.

    Uses `get_department_email` from `department_provider`. If a department
    is not found or the provider raises an error, the department is skipped
    and a warning is logged. No fake/default email addresses are used.
    """
    emails = []
    for dept in departments:
        try:
            addr = get_department_email(dept)
            if addr:
                emails.append(addr)
        except Exception as e:
            logger.warning("Could not get email for department '%s': %s", dept, e)
            continue
    return emails
def gen_email_link(departments,title, content,cclist = []) -> str:
    departments_emails = _get_email_address(departments)
    # 如果沒有任何收件人，回傳友善提示（避免產生無效或測試用的 mailto）
    if not departments_emails:
        logger.info("No email recipients for departments: %s", departments)
        return '<span class="no-email">無可用收件人</span>'

    # 構建 mailto URL
    mailto_url = f'mailto:{",".join(departments_emails)}'

    # 添加參數
    params = []
    params.append(f'subject={_genEmailsubject(title)}')
    params.append(f'body={_genEmailbody(content)}')

    # 如果有副本收件者，添加 cc 參數
    if cclist:
        cc_addrs = _get_email_address(cclist)
        if cc_addrs:
            params.append(f'cc={",".join(cc_addrs)}')

    # 組合完整的 mailto URL
    if params:
        mailto_url += '?' + '&'.join(params)

    return f'<a href="{mailto_url}">Send Email</a>'

def _genEmailbody(content) -> str:
    body_text = f"""請參閱以下公告內容：

{content}

此致

(測試用郵件內容，待修正)"""
    return quote(body_text)

def _genEmailsubject(title) -> str:
    return quote(f"公告通知：{title}")