import re
import configparser
import logging
from mssql_python import connect
from src.db_scripts.schema_definition import TABLE_DEFINITIONS

logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
SQL_CONNECTION_STRING = config['Database']['SQL_CONNECTION_STRING'].replace('"', '')
DB_SCHEMA = config['Database'].get('DB_SCHEMA', 'dbo')
TABLE_NAME = 'messages'
TASKS_TABLE_NAME = 'approval_tasks'

def check_connection():
    try:
        conn = connect(SQL_CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Connection check failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def _validate_schema(schema: str) -> bool:
    # very basic validation: schema can contain letters, numbers and underscores
    return bool(re.match(r'^[A-Za-z0-9_]+$', schema))

def _qname(schema: str, table: str) -> str:
    # return a safe schema-qualified name like [schema].[table]
    return f"[{schema}].[{table}]"

def init_db(schema: str = DB_SCHEMA, force: bool = False):
    logger.info(f"Initializing database with schema: {schema}, force={force}")
    
    if not _validate_schema(schema):
        logger.error(f"Invalid schema name: {schema}")
        return

    # Check if schema is already valid
    if not force:
        try:
            from src.db_scripts.db_utility import validate_database_schema
            if validate_database_schema(schema):
                logger.info("Database schema is valid. No changes made.")
                return
            logger.info("Schema validation failed or force is False. Proceeding with initialization.")
        except ImportError:
            logger.warning("Could not import validate_database_schema. Skipping validation.")

    try:
        conn = connect(SQL_CONNECTION_STRING)
        cursor = conn.cursor()

        # Create schema if missing
        if schema.lower() not in ('dbo', 'guest', 'sys'):
             try:
                cursor.execute(f"IF SCHEMA_ID('{schema}') IS NULL EXEC('CREATE SCHEMA [{schema}]')")
                conn.commit()
             except Exception as e:
                logger.error(f"Create schema failed: {e}")

        # Create Tables based on definition
        # Order matters for Foreign Keys: approval_tasks first, then messages
        creation_order = ['approval_tasks', 'messages']
        
        for table_key in creation_order:
            if table_key not in TABLE_DEFINITIONS:
                continue
                
            definition = TABLE_DEFINITIONS[table_key]
            qname = _qname(schema, table_key)
            
            if force:
                # Drop dependent tables first if dropping approval_tasks
                if table_key == 'approval_tasks':
                     msg_qname = _qname(schema, 'messages')
                     logger.info(f"Dropping dependent table {msg_qname}...")
                     cursor.execute(f"DROP TABLE IF EXISTS {msg_qname}")
                
                logger.info(f"Dropping table {qname}...")
                cursor.execute(f"DROP TABLE IF EXISTS {qname}")
                conn.commit()

            # Check if table exists
            cursor.execute(f"SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?", (schema, table_key))
            if cursor.fetchone():
                logger.info(f"Table {qname} already exists. Checking for schema updates...")
                
                # Check for missing columns
                cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?", (schema, table_key))
                existing_columns = {row[0].lower() for row in cursor.fetchall()}
                
                for col in definition['columns']:
                    col_name = col['name']
                    if col_name.lower() not in existing_columns:
                        logger.info(f"Adding missing column {col_name} to {qname}...")
                        # Note: Adding a column with NOT NULL constraint without DEFAULT value to a non-empty table will fail.
                        # Assuming constraints are handled or table is empty/nullable columns for now.
                        alter_sql = f"ALTER TABLE {qname} ADD {col_name} {col['type']} {col['constraints']}"
                        try:
                            cursor.execute(alter_sql)
                            conn.commit()
                            logger.info(f"Added column {col_name}")
                        except Exception as e:
                            logger.error(f"Failed to add column {col_name}: {e}")
                
                continue

            logger.info(f"Creating table {qname}...")
            columns_sql = []
            for col in definition['columns']:
                columns_sql.append(f"{col['name']} {col['type']} {col['constraints']}")
            
            if 'foreign_keys' in definition:
                for fk in definition['foreign_keys']:
                    ref_parts = fk['references'].split('(')
                    ref_table = ref_parts[0]
                    ref_col = ref_parts[1].rstrip(')')
                    ref_qname = _qname(schema, ref_table)
                    columns_sql.append(f"FOREIGN KEY ({fk['column']}) REFERENCES {ref_qname}({ref_col})")

            create_sql = f"CREATE TABLE {qname} ({', '.join(columns_sql)})"
            cursor.execute(create_sql)
            conn.commit()
            logger.info(f"Created table {qname}")

            # Create Indexes
            if 'indexes' in definition:
                for idx in definition['indexes']:
                    idx_name = idx['name']
                    idx_cols = ", ".join(idx['columns'])
                    try:
                        cursor.execute(f"CREATE INDEX {idx_name} ON {qname} ({idx_cols})")
                        conn.commit()
                        logger.info(f"Created index {idx_name}")
                    except Exception as e:
                        logger.warning(f"Failed to create index {idx_name}: {e}")

        logger.info("Database initialization completed.")

    except Exception as e:
        logger.error(f"init_db failed: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def init_db_create(schema: str = DB_SCHEMA):
    """
    Legacy function for backward compatibility.
    Forces recreation of the database.
    """
    init_db(schema, force=True)
