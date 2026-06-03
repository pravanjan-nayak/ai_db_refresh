from agents.oracle_dba_agent import OracleDBAAgent
from agents.sql_guard import validate_sql
from tools.sql_tool import SQLTool

sql_tool = SQLTool()
agent = OracleDBAAgent()


class WorkflowRouter:

    def route_query(self, question):

        try:

            print(f"\nQUESTION: {question}")

            sql = agent.generate_sql(question)

            print(f"\nGENERATED SQL:\n{sql}")

            validate_sql(sql)

            result = sql_tool.execute_sql(sql)

            return {
                "success": True,
                "sql": sql,
                "result": result.to_dict(orient="records")
            }

        except Exception as e:

            print("\nERROR:")
            print(str(e))

            raise