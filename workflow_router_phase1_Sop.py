from agents.sql_guard import validate_sql
from tools.sql_tool import SQLTool
from db.dba_tasks import match_known_task
from workflows.sop_matcher import match_sop

def parse_sop_sections(content: str):
    sections = {
        "purpose": "",
        "steps": "",
        "commands": "",
        "caution": "",
        "validation": "",
        "other": ""
    }

    current_section = None

    for line in content.splitlines():
        line_strip = line.strip().lower()

        if "## purpose" in line_strip:
            current_section = "purpose"
            continue
        elif "## step" in line_strip:
            current_section = "steps"
            continue
        elif "## command" in line_strip:
            current_section = "commands"
            continue
        elif "## caution" in line_strip:
            current_section = "caution"
            continue
        elif "## validation" in line_strip:
            current_section = "validation"
            continue

        if current_section:
            sections[current_section] += line + "\n"
        else:
            sections["other"] += line + "\n"

    return sections
# Optional LLM advisory fallback
try:
    from agents.oracle_dba_agent import OracleDBAAgent
    agent = OracleDBAAgent()
except Exception:
    agent = None

sql_tool = SQLTool()


def clean_sop_content(content: str) -> str:
    """
    Remove SOP metadata header lines before showing content in UI.
    """
    if not content:
        return ""

    lines = content.splitlines()
    cleaned_lines = []

    metadata_prefixes = (
        "# NAME:",
        "# TITLE:",
        "# KEYWORDS:",
        "# DESCRIPTION:"
    )

    for line in lines:
        if line.strip().startswith(metadata_prefixes):
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


class WorkflowRouter:
    def route_query(self, question):
        try:
            print("\n========== QUERY START ==========")
            print(f"QUESTION: {question}")

            # -------------------------------------------------
            # 0) Basic input validation
            # -------------------------------------------------
            if not question or not str(question).strip():
                return {
                    "success": False,
                    "route": "validation",
                    "task": None,
                    "confidence": 1.00,
                    "sql": None,
                    "result": [],
                    "error": "No input provided.",
                    "explanation": "Please enter a database-related question or SOP request."
                }

            question = str(question).strip()

            # -------------------------------------------------
            # 1) Try deterministic known DBA task mapping first
            # -------------------------------------------------
            print("[STEP 1] Matching known DBA task...")
            task_name, known_sql, meta = match_known_task(question)
            meta = meta or {}
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
                        "This type of request usually requires an operational workflow, SOP, or manual command execution "
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
                    "result": records,
                    "error": None,
                    "explanation": meta.get(
                        "description",
                        f"Matched known DBA task: {task_name}"
                    )
                }

            # -------------------------------------------------
            # 4) No known task matched -> try SOP matching
            # -------------------------------------------------
            print("[STEP 6] No known task matched. Trying SOP match...")
            sop_match = match_sop(question)

            if sop_match.get("matched"):
                print(f"[STEP 6 DONE] SOP matched: {sop_match.get('task')}")
                print("========== QUERY END (SUCCESS: SOP MATCH) ==========")

                cleaned_content = clean_sop_content(sop_match.get("content", ""))

                return {
                    "success": True,
                    "route": "sop",
                    "task": sop_match.get("task"),
                    "confidence": sop_match.get("confidence", 0.85),
                    "sql": None,

                    # Keeps your existing app.py from showing
                    # "Query executed — no rows returned."
                    "result": [
                        {
                            "message": f"SOP matched: {sop_match.get('title')}",
                            "type": "SOP"
                        }
                    ],

                    "error": None,
                    "explanation": (
                        f"Matched SOP: {sop_match.get('title')}\n\n"
                        f"{cleaned_content}"
                    ),
                    "sop_content": cleaned_content,
                    "title": sop_match.get("title")
                }

            # -------------------------------------------------
            # 5) No match -> return reasoning fallback
            # -------------------------------------------------
            print("[STEP 7] No SOP matched. Returning reasoning fallback.")
            explanation = self._build_reasoning_fallback(question)

            return {
                "success": False,
                "route": "reasoning_fallback",
                "task": None,
                "confidence": 0.60,
                "sql": None,
                "result": [],
                "error": "Input not matched to predefined DBA task repository or SOP repository.",
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
                    "that the correct predefined task, SOP, or dictionary view is being used."
                )
            }

    def _build_reasoning_fallback(self, question):
        q = question.strip().lower()

        # -------------------------------------------------
        # Custom explanation for frequent unmatched patterns
        # -------------------------------------------------
        if "index" in q and "size" in q:
            return (
                "From an Oracle DBA perspective, your request appears to mean identifying the largest indexes by storage size.\n\n"
                "In Oracle, index size is commonly derived from segment metadata such as DBA_SEGMENTS.\n\n"
                "Suggested SQL approach:\n\n"
                "SELECT owner,\n"
                "       segment_name AS index_name,\n"
                "       bytes / 1024 / 1024 AS size_mb\n"
                "FROM dba_segments\n"
                "WHERE segment_type = 'INDEX'\n"
                "ORDER BY bytes DESC\n"
                "FETCH FIRST 2 ROWS ONLY;\n\n"
                "If this is a repeated requirement, consider adding it as a predefined known task in db/dba_tasks.py "
                "for deterministic execution."
            )

        if "table" in q and "size" in q:
            return (
                "From an Oracle DBA perspective, your request appears to mean identifying the largest tables by storage size.\n\n"
                "Oracle DBAs typically use segment metadata views such as DBA_SEGMENTS for this analysis.\n\n"
                "Suggested SQL approach:\n\n"
                "SELECT owner,\n"
                "       segment_name AS table_name,\n"
                "       bytes / 1024 / 1024 AS size_mb\n"
                "FROM dba_segments\n"
                "WHERE segment_type = 'TABLE'\n"
                "ORDER BY bytes DESC\n"
                "FETCH FIRST 10 ROWS ONLY;\n\n"
                "If this request is frequently used, it is better to add it as a known task in db/dba_tasks.py."
            )

        # -------------------------------------------------
        # LLM advisory fallback
        # -------------------------------------------------
        if agent:
            try:
                prompt = (
                    "You are an Oracle DBA assistant. "
                    "Interpret the following user request only from an Oracle DBA perspective. "
                    "Do not generate destructive commands. "
                    "Do not assume facts that are not provided. "
                    "If useful, mention relevant Oracle dictionary views, SQL approach, or safe next steps. "
                    "Keep the answer practical, concise, and DBA-focused.\n\n"
                    f"User request: {question}"
                )

                llm_response = agent.generate_response(prompt)

                if llm_response and str(llm_response).strip():
                    return str(llm_response).strip()

            except Exception as llm_error:
                print(f"[LLM FALLBACK ERROR] {llm_error}")

        # -------------------------------------------------
        # Static fallback if LLM is unavailable
        # -------------------------------------------------
        return (
            "Your input is not currently matched to the predefined DBA task repository or SOP repository. "
            "Also, LLM-based Oracle DBA interpretation is currently unavailable. "
            "Please review the request and consider adding it as a known task or SOP for more accurate handling."
        )