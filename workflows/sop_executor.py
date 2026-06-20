# ============================================================
#
# This file handles legacy single-action SOPs, new multi-step
# sequential SOP workflows, and cross-compatibility between
# CDB/PDB and Standalone Non-CDB Oracle environments.
#
# UPDATE: SOPs can now declare which database connection to use via
#         "# DB_CONTEXT:" in the SOP header. Valid values:
#             PDB        -> connect to the pluggable DB service   (default)
#             CDB_ROOT   -> connect to the container root (orcl)  <-- needed for
#                           starting/stopping a PDB, because a closed PDB's own
#                           service is NOT available to connect to.
#             NON_CDB    -> connect to a standalone non-CDB instance
# ============================================================
import re
from db.db_connection import get_connection


def parse_sop_metadata(content: str) -> dict:
    """
    Reads a SOP .md file and extracts:
      - DIAGNOSTIC_SQL  (the SELECT query to run first)
      - ACTION_STEPS    (list of individual tasks split by ---)
      - Execution behavior modifiers (action_mode, stop_on_error)
      - DB_CONTEXT      (which connection to use: PDB / CDB_ROOT / NON_CDB)
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
    db_context = "PDB"  # NEW: default connection context

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

        # NEW: which database connection this SOP should use
        elif stripped.startswith("# DB_CONTEXT:"):
            db_context = stripped.replace("# DB_CONTEXT:", "").strip().upper()

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
        "db_context": db_context,                 # NEW: exposed for connection routing
        "action_template": legacy_template  # Retained to prevent app.py crashes
    }


def build_action_sql(action_template: str, row: dict) -> str:
    """
    Fills placeholders in the action template using the selected row's values.
    """
    sql = action_template
    for key, value in row.items():
        sql = sql.replace("{" + str(key) + "}", str(value) if value is not None else "")
    return sql


def is_multitenant(cursor) -> bool:
    """
    Helper function to inspect if the target database is a Container Database (CDB).
    """
    try:
        cursor.execute("SELECT cdb FROM v$database")
        row = cursor.fetchone()
        return row and row[0] == "YES"
    except Exception:
        # If the view or column doesn't exist, it's a legacy standalone Non-CDB instance.
        return False


def run_sop_diagnostic(sop_name: str, content: str, question: str = "") -> dict:
    """
    Parses the diagnostic SQL out of the markdown content and executes it on Oracle.
    Extracts the targeted username or pdb name from the natural language question if provided.
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
        # CHANGED: connect using the context the SOP asked for (PDB by default,
        # CDB_ROOT for PDB startup/shutdown, etc.)
        conn = get_connection(meta.get("db_context", "PDB"))
        cursor = conn.cursor()

        # Extract target entities from natural language query
        user_match = re.search(r'(?:add|create)\s+user\s+(\w+)', str(question), re.IGNORECASE)
        pdb_match = re.search(r'(?:startup|shutdown|start|stop|open|close|restart|bounce)\s+pdb\s+(\w+)', str(question), re.IGNORECASE)

        if user_match:
            extracted_target = user_match.group(1).upper()
        elif pdb_match:
            extracted_target = pdb_match.group(1).upper()
        else:
            extracted_target = "UNKNOWN"

        # Auto-route container session context if Multitenant is active
        if is_multitenant(cursor):
            # Dynamic fallback: if a user flow, look for an active target PDB context
            # (Note: diagnostic queries check targeted container scopes)
            if user_match and ":username" in diagnostic_sql.lower():
                # Default to ORCLPDB1 if not otherwise bound in downstream mappings
                cursor.execute("ALTER SESSION SET CONTAINER = ORCLPDB")

        # Execute diagnostic with proper bind variable insertion
        if ":username" in diagnostic_sql.lower():
            cursor.execute(diagnostic_sql, username=extracted_target)
        elif ":pdb_name" in diagnostic_sql.lower():
            cursor.execute(diagnostic_sql, pdb_name=extracted_target)
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
    Automatically handles container environments dynamically.
    """
    # Parse source blueprints
    db_context = "PDB"  # NEW: default connection context
    if content:
        meta = parse_sop_metadata(content)
        steps_to_run = meta["action_steps"]
        stop_on_error = meta["stop_on_error"]
        db_context = meta.get("db_context", "PDB")   # NEW: honor SOP-declared context
    else:
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
        # CHANGED: connect using the SOP-declared context
        conn = get_connection(db_context)
        cursor = conn.cursor()

        # ── SMART CONTAINER ROUTING ──────────────────────────────────────────
        # Check instance framework. If CDB architecture is present, alter context.
        # If legacy Standalone database is present, bypass natively.
        if is_multitenant(cursor):
            # Only alter session if we are working on local components like user schemas.
            # Instance tasks like starting/stopping PDBs are executed straight from CDB$ROOT!
            if "pdb" not in sop_name.lower():
                target_pdb = selected_row.get("TARGET_PDB") or selected_row.get("PDB_NAME") or "ORCLPDB"
                cursor.execute(f"ALTER SESSION SET CONTAINER = {target_pdb}")
                print(f"[ROUTER] CDB Framework detected. Session switched to target container: {target_pdb}")
        else:
            print("[ROUTER] Standalone Non-CDB framework detected. Direct execution activated.")
        # ─────────────────────────────────────────────────────────────────────

        for idx, step_blueprint in enumerate(steps_to_run, start=1):
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

     #       try:
      #          cursor.execute(action_sql)
       #         conn.commit()
        #        step_record["status"] = "OK"
         #       steps_executed.append(step_record) 
            try:
                cursor.execute(action_sql)
                # If this step is a query, capture its rows so the UI can display them
                if cursor.description:
                    cols = [c[0] for c in cursor.description]
                    step_record["columns"] = cols
                    step_record["rows"] = [dict(zip(cols, r)) for r in cursor.fetchall()]
                else:
                    conn.commit()
                step_record["status"] = "OK"
                steps_executed.append(step_record)
                
            except Exception as se:
                # Cleaned up disconnection safety shield
                err_text = str(se).lower()
                if any(x in err_text for x in ["not connected", "connection closed", "ora-03114", "ora-03113"]):
                    try:
                        print("[ROUTER] Connection drop detected during state transition. Re-establishing connection...")
                        conn = get_connection(db_context)   # CHANGED: reconnect with same context
                        cursor = conn.cursor()
                        # Retry the statement on the fresh connection
                        cursor.execute(action_sql)
                        conn.commit()
                        step_record["status"] = "OK"
                        steps_executed.append(step_record)
                        continue
                    except Exception as retry_err:
                        se = retry_err  # Overwrite with the actual database error if retry fails

                # Log the failure cleanly if it wasn't a connection issue or if retry failed
                step_record["status"] = "FAILED"
                step_record["error"] = str(se)
                steps_executed.append(step_record)
                overall_success = False
                execution_error = f"Oracle Exception at step {idx}: {str(se)}"

                if stop_on_error:
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
