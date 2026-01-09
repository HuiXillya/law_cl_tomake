import json
import hashlib
import datetime
import logging
from src.db_scripts.db_init import DB_SCHEMA, TABLE_NAME, _qname
from src.db_scripts.db_utility import get_db_connection, fetch_all_as_dict, fetch_one_as_dict

logger = logging.getLogger(__name__)

def get_data_by_title(title: str, schema: str = DB_SCHEMA) -> dict:
    ''' Retrieve a record by title. Returns empty dict if not found. '''
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            title_hash = hashlib.sha256(title.encode('utf-8')).hexdigest()
            qname = _qname(schema, TABLE_NAME)
            cursor.execute(f"SELECT * FROM {qname} WHERE title_hash = ?", (title_hash,))
            rows = fetch_all_as_dict(cursor)
            for row in rows:
                if row['title'] == title:  # Verify actual title matches to handle collisions
                    return row
            return {}
    except Exception as e:
        logger.error(f"get_data_by_title failed: {e}")
        return {}

def insert_message(item: dict) -> bool:
    if not _check_input_date_format(item):
        logger.error("insert_message failed: invalid input format")
        return False
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            dept_json = json.dumps(item['departments'])
            cc_dept_json = json.dumps(item.get('cc_departments', []))
            title_hash = hashlib.sha256(item['title'].encode('utf-8')).hexdigest()
            dt = item.get('datetime', datetime.datetime.now())
            dt_date = datetime.datetime.strptime(item['date'], '%Y-%m-%d') if isinstance(item['date'], str) else item['date']
            qname = _qname(DB_SCHEMA, TABLE_NAME)
            
            # Handle attachments if present
            attachments_json = json.dumps(item.get('attachments', []))

            cursor.execute(f"""
                MERGE {qname} AS target
                USING (VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)) AS source (title, date, link, departments, cc_departments, looked, sended, title_hash, datetime, attachments)
                ON target.title = source.title
                WHEN MATCHED THEN
                    UPDATE SET date = source.date, link = source.link, departments = source.departments, cc_departments = source.cc_departments, looked = source.looked, sended = source.sended, title_hash = source.title_hash, datetime = source.datetime, attachments = source.attachments
                WHEN NOT MATCHED THEN
                    INSERT (title, date, link, departments, cc_departments,  looked, sended, title_hash, datetime, attachments)
                    VALUES (source.title, source.date, source.link, source.departments, source.cc_departments, source.looked, source.sended, source.title_hash, source.datetime, source.attachments);
            """, (item['title'], dt_date, item['link'], dept_json, cc_dept_json, item['looked'], item['sended'], title_hash, dt, attachments_json))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"insert_message failed: {e}")
        return False

def ttl(date_time: datetime.datetime = datetime.datetime.now()) -> None:
    # remove records older than 60 days
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cutoff = date_time - datetime.timedelta(days=60)
            qname = _qname(DB_SCHEMA, TABLE_NAME)
            cursor.execute(f"DELETE FROM {qname} WHERE datetime < ?", (cutoff,))
            conn.commit()
    except Exception as e:
        logger.error(f"ttl failed: {e}")

def _check_input_date_format(input_dict: dict) -> bool:
    required_keys = {'title', 'date','link','departments', 'looked', 'sended'}
    if not required_keys.issubset(input_dict.keys()):
        return False
    
    # Check formats
    if not isinstance(input_dict['title'], str):
        return False
    if isinstance(input_dict['date'], str):
        try:
            datetime.datetime.strptime(input_dict['date'], '%Y-%m-%d')
        except ValueError:
            return False
    elif not isinstance(input_dict['date'], datetime.datetime):
        return False
    if not isinstance(input_dict['link'], str):
        return False
    if not isinstance(input_dict['departments'], list):
        return False
    if not isinstance(input_dict['looked'], bool):
        return False
    if not isinstance(input_dict['sended'], bool):
        return False
    
    return True

def update_message_full(item: dict, task_id: str) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            dept_json = json.dumps(item['departments'])
            cc_dept_json = json.dumps(item.get('cc_departments', []))
            title_hash = hashlib.sha256(item['title'].encode('utf-8')).hexdigest()
            dt = item.get('datetime', datetime.datetime.now())
            dt_date = datetime.datetime.strptime(item['date'], '%Y-%m-%d') if isinstance(item['date'], str) else item['date']
            qname = _qname(DB_SCHEMA, TABLE_NAME)
            
            # Handle attachments
            attachments_json = json.dumps(item.get('attachments', []))

            # Update based on link (assuming unique)
            cursor.execute(f"""
                UPDATE {qname}
                SET title=?, date=?, departments=?, cc_departments=?, looked=?, sended=?, title_hash=?, datetime=?, documentNumber=?, displaySiteName=?, content=?, task_id=?, attachments=?
                WHERE link=?
            """, (item['title'], dt_date, dept_json, cc_dept_json, item['looked'], item['sended'], title_hash, dt, item.get('documentNumber'), item.get('displaySiteName'), item.get('content', ''), task_id, attachments_json, item['link']))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"update_message_full failed: {e}")
        return False

def update_message_department(message_id: int, departments: list, cc_departments: list) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            dept_json = json.dumps(departments)
            cc_dept_json = json.dumps(cc_departments)
            qname = _qname(DB_SCHEMA, TABLE_NAME)
            
            cursor.execute(f"UPDATE {qname} SET departments = ?, cc_departments = ? WHERE id = ?", (dept_json, cc_dept_json, message_id))
            conn.commit()  # Commit transaction
            return True
    except Exception as e:
        logger.error(f"update_message_department failed: {e}")
        return False

def get_message_by_link(link: str, schema: str = DB_SCHEMA) -> dict:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            qname = _qname(schema, TABLE_NAME)
            # Assuming link is unique enough or we just want one
            cursor.execute(f"SELECT * FROM {qname} WHERE link = ?", (link,))
            return fetch_one_as_dict(cursor) or {}
    except Exception as e:
        logger.error(f"get_message_by_link failed: {e}")
        return {}

def get_message_by_id(msg_id: int, schema: str = DB_SCHEMA) -> dict:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            qname = _qname(schema, TABLE_NAME)
            cursor.execute(f"SELECT * FROM {qname} WHERE id = ?", (msg_id,))
            return fetch_one_as_dict(cursor) or {}
    except Exception as e:
        logger.error(f"get_message_by_id failed: {e}")
        return {}

def update_message_task(message_id: int, task_id: str) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            qname = _qname(DB_SCHEMA, TABLE_NAME)
            cursor.execute(f"UPDATE {qname} SET task_id = ? WHERE id = ?", (task_id, message_id))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"update_message_task failed: {e}")
        return False

def insert_message_with_task(item: dict, task_id: str) -> bool:
    if not _check_input_date_format(item):
        logger.error("insert_message_with_task failed: invalid input format")
        return False
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            dept_json = json.dumps(item['departments'])
            cc_dept_json = json.dumps(item.get('cc_departments', []))
            title_hash = hashlib.sha256(item['title'].encode('utf-8')).hexdigest()
            dt = item.get('datetime', datetime.datetime.now())
            dt_date = datetime.datetime.strptime(item['date'], '%Y-%m-%d') if isinstance(item['date'], str) else item['date']
            qname = _qname(DB_SCHEMA, TABLE_NAME)
            
            # Handle attachments
            attachments_json = json.dumps(item.get('attachments', []))

            cursor.execute(f"""
                INSERT INTO {qname} (title, date, link, departments, cc_departments, looked, sended, title_hash, datetime, documentNumber, displaySiteName, content, task_id, attachments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item['title'], dt_date, item['link'], dept_json, cc_dept_json, item['looked'], item['sended'], title_hash, dt, item.get('documentNumber'), item.get('displaySiteName'), item.get('content', ''), task_id, attachments_json))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"insert_message_with_task failed: {e}")
        return False
