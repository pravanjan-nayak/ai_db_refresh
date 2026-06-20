# ============================================================
#
# This file handles both legacy single-action SOPs and new 
# multi-step sequential SOP workflows seamlessly.
# ============================================================
import re
from db.db_connection import get_connection


def parse_sop_metadata(content: str) -> dict:
    """
    Reads a SOP .md file and extracts:
      - DIAGNOSTIC_SQL  (the SELECT query to run first)
      - ACTION_STEPS    (list of individual tasks split by ---)
      - Execution behavior modifiers (action_mode, stop_on_error)
      - action_required, approval_required flags
    """
    lines = content.splitlines()

    diagnostic_lines = []
    in_diagnostic_block = False
    action_required = False
    approval_required = False
    
    # New Multi-Step Defaults
    action_steps = []
    action_mode = "sequential"
    stop_on_error = True
    legacy_template = None

    for line in lines:
        stripped = line.strip()

        if stripped == "# DIAGNOSTIC_SQL_START":
            in_diagnostic_block = True
            continue

        if stripped == "# DIAGNOSTIC_SQL_END":
            in_diagnostic_block = False
            continue

        if in_diagnostic_block:
            diagnostic_lines.append(line)
            continue

        if stripped.startswith("# ACTION_REQUIRED:"):
            action_required = stripped.replace("# ACTION_REQUIRED:", "").strip().lower() == "true"

        elif stripped.startswith("# APPROVAL_REQUIRED:"):
            approval_required = stripped.replace("# APPROVAL_REQUIRED:", "").strip().lower() == "true"

        elif stripped.startswith("# ACTION_MODE:"):
            action_mode = stripped.replace("# ACTION_MODE:", "").strip().lower()

        elif stripped.startswith("# STOP_ON_ERROR:"):
            stop_on_error = stripped.replace("# STOP_ON_ERROR:", "").strip().lower() == "true"

        # Backward compatibility fallback
        elif stripped.startswith("# ACTION_TEMPLATE:"):
            legacy_template = stripped.replace("# ACTION_TEMPLATE:", "").strip()

    # Extract DIAGNOSTIC_SQL block
    diagnostic_sql = "\n".join(diagnostic_lines).strip() if diagnostic_lines else None

    # Extract New Multi-Step ACTION_SQL block using regex block searching
    action_match = re.search(r'# ACTION_SQL_START\s*(.*?)\s*# ACTION_SQL_END', content, re.DOTALL)
    if action_match:
        raw_actions = action_match.group(1).strip()
        # Cleanly divide tasks based on our new triple-dash line delimiter
        action_steps = [step.strip() for step in raw_actions.split("---") if step.strip()]
    elif legacy_template:
        # Gracefully drop legacy templates into our execution queue array
        action_steps = [legacy_template]

    return {
        "diagnostic_sql": diagnostic_sql,
        "action_required": action_required,
        "approval_required": approval_required,
        "action_steps": action_steps,
        "action_mode": action_mode,
        "stop_on_error": stop_on_error,
        "action_template": legacy_template # Retained to prevent app.py crashes
    }


def build_action_sql(action_template: str, row: dict) -> str:
    """
    Fills placeholders in the action template using the selected row's values.
    """
    sql = action_template
    for key, value in row.items():
        sql = sql.replace("{" + str(key) + "}", str(value) if value is not None else "")
    return sql


def run_sop_diagnostic(sop_name: str, content: str, question: str = "") -> dict:
    """
    Parses the diagnostic SQL out of the markdown content and executes it on Oracle.
    Extracts the targeted username from the natural language question if provided.
    """
    meta = parse_sop_metadata(content)
    diagnostic_sql = meta["diagnostic_sql"]

    if not diagnostic_sql:
        return {
            "success": False,
            "error": "No diagnostic SQL found in this SOP metadata configuration.",
            "rows": []
        }

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Look for phrases like "add user <USERNAME>" or "create user <USERNAME>"
        match = re.search(r'(?:add|create)\s+user\s+(\w+)', str(question), re.IGNORECASE)
        
        if match:
            extracted_username = match.group(1).upper()
        else:
            extracted_username = "UNKNOWN"

        # Check if the query expects a bind variable named :username
        if ":username" in diagnostic_sql.lower():
            cursor.execute(diagnostic_sql, username=extracted_username)
        else:
            cursor.execute(diagnostic_sql)

        # Fetch results
        columns = [col[0] for col in cursor.description]
        rows = []
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, row)))

        cursor.close()
        conn.close()

        return {
            "success": True,
            "sop_name": sop_name,
            "diagnostic_sql": diagnostic_sql,
            "rows": rows,
            "columns": columns,
            "row_count": len(rows),
            "action_required": meta["action_required"],
            "action_template": meta["action_template"], 
            "action_steps": meta["action_steps"],          # Exposed for UI checkbox pipeline
            "action_mode": meta["action_mode"],            # Exposed for UI tracking
            "stop_on_error": meta["stop_on_error"],        # Exposed for UI tracking
            "approval_required": meta["approval_required"],
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "sop_name": sop_name,
            "diagnostic_sql": diagnostic_sql,
            "rows": [],
            "columns": [],
            "row_count": 0,
            "action_required": meta["action_required"],
            "action_template": meta["action_template"],
            "approval_required": meta["approval_required"],
            "error": f"{type(e).__name__}: {str(e)}"
        }


def run_sop_action(action_template: str, selected_row: dict, sop_name: str, approved_by: str = "DBA", content: str = None) -> dict:
    """
    Executes an array of sequential statements or falls back to a legacy single command.
    """
    # If full file content is provided, parse it to extract the structured multi-step payload
    if content:
        meta = parse_sop_metadata(content)
        steps_to_run = meta["action_steps"]
        stop_on_error = meta["stop_on_error"]
    else:
        # FIX: Check if the string template contains multi-step delimiters ('---'). 
        # If it does, safely chop it into separate commands so Oracle can run them individually.
        if action_template and "---" in action_template:
            steps_to_run = [step.strip() for step in action_template.split("---") if step.strip()]
        else:
            steps_to_run = [action_template] if action_template else []
        stop_on_error = True

    steps_executed = []
    overall_success = True
    combined_sql_log = []
    execution_error = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        for idx, step_blueprint in enumerate(steps_to_run, start=1):
            # Parse dynamic data properties out of the diagnostic row keys
            try:
                action_sql = step_blueprint.format(**selected_row)
            except KeyError as ke:
                overall_success = False
                execution_error = f"Placeholder formatting mismatch on Step {idx}: Missing column variable {str(ke)}"
                steps_executed.append({"step": idx, "sql": step_blueprint, "status": "SKIPPED_ERROR"})
                if stop_on_error:
                    break
                continue

            combined_sql_log.append(action_sql)
            step_record = {"step": idx, "sql": action_sql, "status": "PENDING"}

            try:
                cursor.execute(action_sql)
                conn.commit()  # Keeps mixed DML sequences clean and segmented
                step_record["status"] = "OK"
                steps_executed.append(step_record)
            except Exception as se:
                step_record["status"] = "FAILED"
                step_record["error"] = str(se)
                steps_executed.append(step_record)
                overall_success = False
                execution_error = f"Oracle Exception at step {idx}: {str(se)}"
                
                if stop_on_error:
                    # Halt processing immediately; downstream tasks become skipped fields
                    for skipped_idx in range(idx + 1, len(steps_to_run) + 1):
                        steps_executed.append({
                            "step": skipped_idx, 
                            "sql": steps_to_run[skipped_idx - 1], 
                            "status": "HALTED"
                        })
                    break

        cursor.close()
        conn.close()

        return {
            "success": overall_success,
            "sop_name": sop_name,
            "action_sql": "\n---\n".join(combined_sql_log),
            "steps_executed": steps_executed,
            "message": f"Execution pipeline completed by {approved_by}." if overall_success else "Pipeline halted with execution errors.",
            "error": execution_error
        }

    except Exception as e:
        return {
            "success": False,
            "sop_name": sop_name,
            "action_sql": action_template,
            "steps_executed": steps_executed,
            "message": "Failed to safely initiate database pipeline connection wrapper.",
            "error": f"{type(e).__name__}: {str(e)}"
        }