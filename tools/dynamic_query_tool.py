import pandas as pd

from tools.base_tool import BaseTool
from db.dynamic_connection import (
    get_connection
)


class DynamicQueryTool(BaseTool):

    name = "dynamic_query_tool"

    description = (
        "Execute SQL against any Oracle database"
    )

    def run(
        self,
        username,
        password,
        tns_alias,
        query
    ):

        conn = get_connection(
            username,
            password,
            tns_alias
        )

        try:

            df = pd.read_sql(
                query,
                conn
            )

            return df

        finally:

            conn.close()