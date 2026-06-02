from tools.dynamic_query_tool import (
    DynamicQueryTool
)


class DynamicValidationAgent:

    def __init__(self):

        self.query_tool = (
            DynamicQueryTool()
        )

    def validate_schema(
        self,
        username,
        password,
        tns_alias,
        schema_name
    ):

        schema_name = (
            schema_name.upper()
        )

        exists_query = f"""
        SELECT username
        FROM dba_users
        WHERE username = '{schema_name}'
        """

        result = self.query_tool.run(
            username,
            password,
            tns_alias,
            exists_query
        )

        exists = len(result) > 0

        if not exists:

            return {
                "database": tns_alias,
                "schema": schema_name,
                "exists": False,
                "object_count": 0
            }

        count_query = f"""
        SELECT COUNT(*) OBJECT_COUNT
        FROM dba_objects
        WHERE owner = '{schema_name}'
        """

        count_result = self.query_tool.run(
            username,
            password,
            tns_alias,
            count_query
        )

        object_count = int(
            count_result.iloc[0][
                "OBJECT_COUNT"
            ]
        )

        return {

            "database": tns_alias,

            "schema": schema_name,

            "exists": True,

            "object_count": object_count
        }