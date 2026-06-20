# ============================================================
# FILE:    workflows\sop_executor.py
# ACTION:  CREATE THIS AS A NEW FILE
# LOCATION: C:\AI Agents\OracleAIDBAAgent-main\OracleAIDBAAgent-main\workflows\sop_executor.py
#
# This file does NOT need changes when new SOPs are added.
# It reads whatever SQL is in the .md file automatically.
# ============================================================
import re
from db.db_connection import get_connection


def parse_sop_metadata(content: str) -> dict:
    """
    Reads a SOP .md file and extracts:
      - DIAGNOSTIC_SQL  (the SELECT query to run first)
      - ACTION_TEMPLATE (the ALTER/DDL to run after approval)
      - action_required, approval_required flags
    """
    lines = content.splitlines()

    diagnostic_lines = []
    in_diagnostic_block = False
    action_required = False
    action_template = None
    approval_required = False

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

        elif stripped.startswith("# ACTION_TEMPLATE:"):
            action_template = stripped.replace("# ACTION_TEMPLATE:", "").strip()

        elif stripped.startswith("# APPROVAL_REQUIRED:"):
            approval_required = stripped.replace("# APPROVAL_REQUIRED:", "").strip().lower() == "true"

    diagnostic_sql = "\n".join(diagnostic_lines).strip() if diagnostic_lines else None

    return {
        "diagnostic_sql": diagnostic_sql,
        "action_required": action_required,
        "action_template": action_template,
        "approval_required": approval_required
    }


def build_action_sql(action_template: str, row: dict) -> str:
    """
    Fills placeholders in the action template using the selected row's values.
    Example:
      template: ALTER SYSTEM KILL SESSION '{sid},{serial#}' IMMEDIATE
      row:      {"sid": "42", "serial#": "1234"}
      result:   ALTER SYSTEM KILL SESSION '42,1234' IMMEDIATE
    """
    sql = action_template
    for key, value in row.items():
        sql = sql.replace("{" + str(key) + "}", str(value) if value is not None else "")
    return sql

###############Newly added
import re  # Ensure 'import re' is at the top of workflows/sop_executor.py

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

        # =================================================================
        # NEW DYNAMIC BIND REPLACEMENT LOGIC
        # =================================================================
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
            # Fallback if no placeholder bind exists in the .md file block
            cursor.execute(diagnostic_sql)
        # =================================================================

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

def run_sop_action(action_template: str, selected_row: dict, sop_name: str, approved_by: str = "DBA") -> dict:
    """
    Executes the generated DDL action against Oracle when the DBA clicks Approve.
    """
    try:
        # 1. Format the blueprint template using the checked table row keys
        # Example: "CREATE USER {TARGET_USERNAME}..." -> "CREATE USER DUMMY..."
        action_sql = action_template.format(**selected_row)
        
        # 2. Run the command against Oracle
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(action_sql)
        cursor.close()
        conn.close()

        # =====================================================================
        # 🔑 CRITICAL: THIS RETURN DICTIONARY MUST MATCH YOUR app.py KEYS
        # =====================================================================
        return {
            "success": True,
            "sop_name": sop_name,
            "action_sql": action_sql,  # <-- Matches 'if "action_sql" in result'
            "message": f"🎉 Success! User profile provisioned successfully by {approved_by}.", # <-- Matches 'if "message" in result'
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "sop_name": sop_name,
            "action_sql": action_template, 
            "message": "Failed to execute database action.",
            "error": f"{type(e).__name__}: {str(e)}"
        }
