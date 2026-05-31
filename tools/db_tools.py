import pandas as pd
from db.db_connection import get_connection
from db.dba_tasks import DBA_TASKS

def run_dba_task(task_name):
    if task_name not in DBA_TASKS:
        return f"Unknown DBA task: {task_name}"

    query = DBA_TASKS[task_name]["query"]

    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()

    return df

from db.dba_tasks import DBA_TASKS
from db.db_connection import get_connection
import pandas as pd

def get_db_summary():
    summary = {}

    important_tasks = [
        "database_status",
        "top_waits",
        "active_sessions",
        "tablespace_usage",
        "top_sql"
    ]

    for task in important_tasks:
        try:
            query = DBA_TASKS[task]["query"]
            conn = get_connection()
            df = pd.read_sql(query, conn)
            conn.close()
            summary[task] = df
        except Exception as e:
            summary[task] = f"Error: {str(e)}"

    return summary
