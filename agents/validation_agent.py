from tools.query_tool import QueryTool


class ValidationAgent:

    def __init__(self):

        self.query_tool = QueryTool()

    def validate_schema(
        self,
        env_name,
        schema_name
    ):

        schema_name = schema_name.upper()

        exists_query = f"""
        SELECT username
        FROM dba_users
        WHERE username = '{schema_name}'
        """

        result = self.query_tool.run(
            env_name,
            exists_query
        )

        exists = len(result) > 0

        if not exists:

            return {
                "environment": env_name,
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
            env_name,
            count_query
        )

        object_count = int(
            count_result.iloc[0]["OBJECT_COUNT"]
        )

        return {
            "environment": env_name,
            "schema": schema_name,
            "exists": True,
            "object_count": object_count
        }