import pandas as pd

from tools.base_tool import BaseTool
from db.connection_manager import get_connection


class QueryTool(BaseTool):

    name = "query_tool"

    description = "Execute ad-hoc SQL queries"

    def run(
        self,
        env_name,
        query
    ):

        conn = get_connection(
            env_name
        )

        try:

            df = pd.read_sql(
                query,
                conn
            )

            return df

        finally:

            conn.close()