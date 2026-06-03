import pandas as pd

from tools.base_tool import BaseTool
from db.db_connection import get_connection
from db.dba_tasks import DBA_TASKS


class SQLTool(BaseTool):

    name = "sql_tool"
    description = "Execute Oracle DBA SQL tasks"

    def run(self, task_name):

        if task_name not in DBA_TASKS:
            raise Exception(
                f"Unknown task: {task_name}"
            )

        query = DBA_TASKS[task_name]["query"]

        return self.execute_sql(query)

    def execute_sql(self, query):

        conn = get_connection()

        try:
            df = pd.read_sql(query, conn)
            return df

        finally:
            conn.close()