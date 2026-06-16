from agents.sql_guard import validate_sql
from tools.sql_tool import SQLTool
from db.dba_tasks import match_known_task

sql_tool = SQLTool()


class WorkflowRouter:

    def route_query(self, question):
        try:
            print("\n========== QUERY START ==========")
            print(f"QUESTION: {question}")

            # -------------------------------------------------
            # 1) Try deterministic known DBA task mapping first
            # -------------------------------------------------
            print("[STEP 1] Matching known task...")
            task_name, known_sql, meta = match_known_task(question)
            print(f"[STEP 1 DONE] task_name={task_name}, known_sql_found={bool(known_sql)}")

            # -------------------------------------------------
            # 2) Known task found but not query-based
            # -------------------------------------------------
            if task_name and not known_sql:
                print("[STEP 2] Known task matched but no SQL (action-only task)")

                return {
                    "success": False,
                    "route": "known_task",
                    "task": task_name,
                    "confidence": meta.get("confidence", 0.90),
                    "sql": None,
                    "result": [],
                    "error": f"Task '{task_name}' is recognized, but it is not a query-based task.",
                    "explanation": (
                        f"The request is recognized as '{task_name}', but it is not a direct SQL query task. "
                        "This type of request usually requires an operational workflow or command execution "
                        "instead of a database SELECT statement."
                    )
                }

            # -------------------------------------------------
            # 3) Known task found with SQL -> validate and execute
            # -------------------------------------------------
            if known_sql:
                print("[STEP 3] Using known task SQL")
                sql = known_sql.strip()
                route = "known_task"
                confidence = meta.get("confidence", 0.95)

                print(f"[SQL]\n{sql}")

                print("[STEP 4] Validating SQL...")
                validate_sql(sql)
                print("[STEP 4 DONE] SQL valid")

                print("[STEP 5] Executing SQL...")
                result = sql_tool.execute_sql(sql)
                print("[STEP 5 DONE] SQL execution completed")

                if hasattr(result, "to_dict"):
                    records = result.to_dict(orient="records")
                elif isinstance(result, list):
                    records = result
                else:
                    records = [{"result": str(result)}]

                print("========== QUERY END (SUCCESS: KNOWN TASK) ==========")

                return {
                    "success": True,
                    "route": route,
                    "task": task_name,
                    "confidence": confidence,
                    "sql": sql,
                    "result": records
                }

            # -------------------------------------------------
            # 4) No known task matched
            #    Return DBA explanation only
            #    (No AI SQL generation, no SQL execution fallback)
            # -------------------------------------------------
            print("[STEP 6] No known task matched. Returning reasoning fallback.")

            explanation = self._build_reasoning_fallback(question)

            return {
                "success": False,
                "route": "reasoning_fallback",
                "task": None,
                "confidence": 0.60,
                "sql": None,
                "result": [],
                "error": "Input not matched to predefined DBA repository.",
                "explanation": explanation
            }

        except Exception as e:
            print("\n========== QUERY ERROR ==========")
            print(str(e))
            print("=================================\n")

            return {
                "success": False,
                "route": "error",
                "task": None,
                "confidence": 0.0,
                "sql": None,
                "result": [],
                "error": str(e),
                "explanation": (
                    "The request could not be completed. "
                    "Please review the input from an Oracle DBA perspective and verify "
                    "that the correct predefined task or dictionary view is being used."
                )
            }

    def _build_reasoning_fallback(self, question):
        q = question.strip().lower()

        # -------------------------------------------------
        # Custom friendly explanation for common unmatched patterns
        # -------------------------------------------------
        if "index" in q and "size" in q:
            return (
                "Your input is not currently matched to the predefined DBA repository. "
                "From an Oracle DBA perspective, your request appears to mean finding the largest indexes by storage size. "
                "\n\n"
                "In Oracle, index size is usually derived from segment metadata, typically using DBA_SEGMENTS, "
                "not from ALL_INDEXES.LENGTH. "
                "\n\n"
                "A suggested SQL approach would be:\n\n"
                "SELECT owner,\n"
                "       segment_name AS index_name,\n"
                "       bytes / 1024 / 1024 AS size_mb\n"
                "FROM dba_segments\n"
                "WHERE segment_type = 'INDEX'\n"
                "ORDER BY bytes DESC\n"
                "FETCH FIRST 2 ROWS ONLY;\n\n"
                "Explanation:\n"
                "- An index is a database object used to improve query performance.\n"
                "- 'Top 2 index in size' usually means the two largest index segments in storage.\n"
                "- Size information comes from segment views such as DBA_SEGMENTS."
            )

        if "table" in q and "size" in q:
            return (
                "Your input is not currently matched to the predefined DBA repository. "
                "From an Oracle DBA perspective, you appear to be asking for the largest tables by storage size. "
                "\n\n"
                "Oracle DBAs usually use DBA_SEGMENTS for table segment size analysis. "
                "A common query pattern is:\n\n"
                "SELECT owner,\n"
                "       segment_name AS table_name,\n"
                "       bytes / 1024 / 1024 AS size_mb\n"
                "FROM dba_segments\n"
                "WHERE segment_type = 'TABLE'\n"
                "ORDER BY bytes DESC\n"
                "FETCH FIRST 10 ROWS ONLY;"
            )

        # -------------------------------------------------
        # Generic fallback
        # -------------------------------------------------
        return (
            "Your input is not currently matched to the predefined DBA repository. "
            "From an Oracle DBA perspective, this appears to be a custom request. "
            "Please review the correct Oracle dictionary views or add this requirement "
            "as a predefined DBA task for more accurate execution.\n\n"
            "Suggested next step:\n"
            "- Add this request as a known task in db/dba_tasks.py if it is frequently used.\n"
            "- Or rewrite the question more explicitly, for example by specifying schema, object type, or metric."
        )