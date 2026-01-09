import logging
import datetime
import configparser
from mssql_python import connect

logger = logging.getLogger(__name__)

from src.db_scripts.db_utility import db_row_to_dict
from src.string_management import TasksKey, AnnKey
from src.htmx_gen import gen_looked
def lookup_db():
    # select data from the database in these two months
    config = configparser.ConfigParser()
    config.read('config.ini')
    DB_SCHEMA = config['Database'].get('DB_SCHEMA', 'dbo')
    qname = f"[{DB_SCHEMA}].[messages]"
    SQL_CONNECTION_STRING = config['Database']['SQL_CONNECTION_STRING'].replace('"', '')
    try:
        conn = connect(SQL_CONNECTION_STRING)
        # to do: select data from the database
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {qname}")
        rows = cursor.fetchall()
        ann_list = []
        for row in rows:
            ann = db_row_to_dict(row)
            if ann.get(AnnKey.SENDED.value):
                ann_list.append(ann)
        #sort ann_list by date desc
        # ann_list.sort(key=lambda x: x.get('date', datetime.datetime.min), reverse=True)
        return gen_looked(ann_list)
    except Exception as e:
        logger.error(f"Database lookup failed: {e}")
        return "<div>Error accessing the database.</div>"
    finally:
        if 'conn' in locals():
            conn.close()