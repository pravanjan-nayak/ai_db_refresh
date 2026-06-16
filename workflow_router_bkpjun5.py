from agents.oracle_dba_agent import OracleDBAAgent
from agents.sql_guard import validate_sql
from tools.sql_tool import SQLTool
from db.dba_tasks import match_known_task

sql_tool = SQLTool()
agent = OracleDBAAgent()


class WorkflowRouter:

    def route_query(self, question):

        try:
            print(f"\nQUESTION: {question}")

            # -------------------------------------------------
            # 1) First try deterministic known DBA task mapping
            # -------------------------------------------------
            task_name, known_sql, meta = match_known_task(question)

            if known_sql:
                sql = known_sql.strip()
                route = "known_task"
                confidence = meta.get("confidence", 0.99)

                print(f"\nROUTE: {route}")
                print(f"TASK: {task_name}")
                print(f"CONFIDENCE: {confidence}")
                print(f"\nSQL FROM KNOWN TASK:\n{sql}")

            else:
                # ---------------------------------------------
                # 2) Fallback to AI-generated SQL
                # ---------------------------------------------
                route = "llm_fallback"
                task_name = None
                confidence = 0.70

                sql = agent.generate_sql(question)

                if not sql or str(sql).strip().upper() == "INSUFFICIENT_CONTEXT":
                    return {
                        "success": False,
                        "route": route,
                        "task": task_name,
                        "confidence": 0.30,
                        "sql": None,
                        "result": [],
                        "error": "Unable to determine exact SQL from available metadata/context."
                    }

                sql = str(sql).strip()

                print(f"\nROUTE: {route}")
                print(f"CONFIDENCE: {confidence}")
                print(f"\nGENERATED SQL:\n{sql}")

            # -------------------------------------------------
            # 3) Validate SQL
            # -------------------------------------------------
            validate_sql(sql)

            # -------------------------------------------------
            # 4) Execute SQL
            # -------------------------------------------------
            result = sql_tool.execute_sql(sql)

            # -------------------------------------------------
            # 5) Convert result safely
            # -------------------------------------------------
            if hasattr(result, "to_dict"):
                records = result.to_dict(orient="records")
            elif isinstance(result, list):
                records = result
            else:
                records = [{"result": str(result)}]

            return {
                "success": True,
                "route": route,
                "task": task_name,
                "confidence": confidence,
                "sql": sql,
                "result": records
            }

        except Exception as e:
            print("\nERROR:")
            print(str(e))

            return {
                "success": False,
                "route": "error",
                "task": None,
                "confidence": 0.0,
                "sql": None,
                "result": [],
                "error": str(e)
            }