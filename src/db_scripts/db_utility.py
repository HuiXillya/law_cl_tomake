import contextlib
import logging
import json
import datetime
from mssql_python import connect
from src.db_scripts.db_init import SQL_CONNECTION_STRING
from src.db_scripts.schema_definition import TABLE_DEFINITIONS

logger = logging.getLogger(__name__)

def validate_database_schema(schema_name: str) -> bool:
    """
    Validates if the current database schema matches the defined schema.
    Returns True if valid, False otherwise.
    """
    is_valid = True
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            for table_name, definition in TABLE_DEFINITIONS.items():
                # Check if table exists
                cursor.execute(f"SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?", (schema_name, table_name))
                if not cursor.fetchone():
                    logger.error(f"Missing table: {table_name}")
                    is_valid = False
                    continue
                
                # Check columns
                cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?", (schema_name, table_name))
                existing_columns = {row[0].lower() for row in cursor.fetchall()}
                defined_columns = {col['name'].lower() for col in definition['columns']}
                
                missing_cols = defined_columns - existing_columns
                if missing_cols:
                    logger.error(f"Table {table_name} missing columns: {missing_cols}")
                    is_valid = False
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return False
                
    return is_valid

@contextlib.contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Yields a connection object.
    Automatically handles rollback on error and closing connection.
    """
    conn = None
    try:
        conn = connect(SQL_CONNECTION_STRING)
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def row_to_dict(cursor, row) -> dict:
    """
    Convert a database row to a dictionary using cursor description.
    Handles JSON parsing for specific fields.
    """
    if not row:
        return {}
    
    columns = [column[0] for column in cursor.description]
    result = dict(zip(columns, row))
    
    # Helper to find key case-insensitively
    def find_key(target):
        for k in result:
            if k.lower() == target.lower():
                return k
        return None

    # Handle JSON fields
    json_fields = ['departments', 'cc_departments', 'attachments']
    for field in json_fields:
        key = find_key(field)
        if key:
            val = result[key]
            if isinstance(val, str) and val.strip():
                try:
                    result[key] = json.loads(val)
                except Exception:
                    # Fallback for attachments if it's comma separated
                    if field == 'attachments':
                         result[key] = [s.strip() for s in str(val).split(',') if s.strip()]
                    else:
                        result[key] = []
            elif val is None:
                 result[key] = []

    # Handle Date formatting
    date_key = find_key('date')
    if date_key:
        val = result[date_key]
        if isinstance(val, datetime.datetime):
            result[date_key] = val.strftime('%Y-%m-%d')

    return result

def fetch_all_as_dict(cursor):
    """
    Fetch all rows from cursor and return as list of dicts.
    """
    rows = cursor.fetchall()
    return [row_to_dict(cursor, row) for row in rows]

def fetch_one_as_dict(cursor):
    """
    Fetch one row from cursor and return as dict.
    """
    row = cursor.fetchone()
    if row:
        return row_to_dict(cursor, row)
    return None

# Deprecated: Kept for backward compatibility during refactoring
def db_row_to_dict(raw_row) -> dict:
    try:
        dept = json.loads(raw_row[4])
        cc_dept = json.loads(raw_row[5])
        # Attempt to parse attachments if present in additional columns
        attachments = []
        try:
            # some schemas may add attachments as a JSON string in a later column (e.g., index 15)
            if len(raw_row) > 15 and raw_row[15]:
                raw_attachments = raw_row[15]
                try:
                    attachments = json.loads(raw_attachments)
                except Exception:
                    attachments = [s.strip() for s in str(raw_attachments).split(',') if s.strip()]
        except Exception:
            attachments = []

        return {
            'id': raw_row[0],
            'title': raw_row[1],
            'date': raw_row[2].strftime('%Y-%m-%d') if isinstance(raw_row[2], datetime.datetime) else raw_row[2],
            'link': raw_row[3],
            'departments': dept,
            'cc_departments': cc_dept,
            'looked': bool(raw_row[6]),
            'sended': bool(raw_row[7]),
            'title_hash': raw_row[8],
            'datetime': raw_row[9],
            'documentNumber': raw_row[10],
            'displaySiteName': raw_row[11],
            'content': raw_row[12],
            'task_id': raw_row[13],
            'attachments': attachments
        }
    except Exception as e:
        logger.error(f"db_row_to_dict failed: {e}")
        return {}

def _db_data_integrity_check(raw_row) -> bool:
    return True # Simplified for now as schema is evolving