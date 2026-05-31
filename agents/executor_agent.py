from tools.sql_tool import SQLTool

sql_tool = SQLTool()


def execute_plan(plan):

    if plan == "DATABASE_STATUS":
        return sql_tool.run(
            "database_status"
        )

    if plan == "ACTIVE_SESSIONS":
        return sql_tool.run(
            "active_sessions"
        )

    if plan == "TOP_SQL":
        return sql_tool.run(
            "top_sql"
        )

    if plan == "TABLESPACE_USAGE":
        return sql_tool.run(
            "tablespace_usage"
        )

    return f"Plan not implemented: {plan}"