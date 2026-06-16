from typing import Dict, Any, Optional, Callable

from workflows.approval_store import (
    get_approval_request,
    update_execution_status
)


def _build_result(
    success: bool,
    request_id: str,
    execution_status: str,
    message: str,
    request_record: Optional[Dict[str, Any]] = None,
    statement_preview: str = "",
    verification_result: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    return {
        "success": success,
        "request_id": request_id,
        "execution_status": execution_status,
        "message": message,
        "request_record": request_record or {},
        "statement_preview": statement_preview,
        "verification_result": verification_result or {}
    }


def _basic_verification_from_request(request_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safe verification placeholder.
    This does NOT query/change the DB.
    It verifies that a usable reviewed plan exists.
    """
    planner_result = request_record.get("planner_result", {})
    recommendation = planner_result.get("recommendation", {})

    checks = []

    statement_preview = recommendation.get("statement_preview", "")
    recommended_file_path = recommendation.get("recommended_file_path", "")
    tablespace_name = planner_result.get("tablespace_name", "")

    checks.append({
        "name": "statement_preview_present",
        "status": "PASS" if bool(statement_preview) else "FAIL",
        "details": "Reviewed statement preview is present." if statement_preview else "Reviewed statement preview is missing."
    })

    checks.append({
        "name": "recommended_file_path_present",
        "status": "PASS" if bool(recommended_file_path) else "FAIL",
        "details": f"Recommended file path = {recommended_file_path}" if recommended_file_path else "Recommended file path is missing."
    })

    checks.append({
        "name": "tablespace_name_present",
        "status": "PASS" if bool(tablespace_name) else "FAIL",
        "details": f"Tablespace = {tablespace_name}" if tablespace_name else "Tablespace name is missing."
    })

    all_pass = all(item["status"] == "PASS" for item in checks)

    return {
        "success": all_pass,
        "checks": checks,
        "mode": "SAFE_PLACEHOLDER"
    }


def execute_approved_change_request(
    request_id: str,
    conn=None,
    dry_run: bool = True,
    executor_callback: Optional[Callable[[Any, Dict[str, Any], str], Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Safe execution orchestrator for approved requests.

    Parameters
    ----------
    request_id : str
        Approved request ID from approval_store.json
    conn : optional
        DB connection object for future approved executor callback use
    dry_run : bool
        True => safe simulation only, no DB change
    executor_callback : callable
        Enterprise-approved external executor function.
        Expected signature:
            executor_callback(conn, request_record, statement_preview) -> dict

        The callback is NOT implemented here intentionally.
        This step only provides the orchestration hook.

    Returns
    -------
    dict
        Structured execution result.
    """
    request_record = get_approval_request(request_id)

    if not request_record:
        return _build_result(
            success=False,
            request_id=request_id,
            execution_status="FAILED",
            message=f"Request ID not found: {request_id}"
        )

    approval_status = request_record.get("approval_status", "")
    current_execution_status = request_record.get("execution_status", "")
    policy_result = request_record.get("policy_result", {})
    planner_result = request_record.get("planner_result", {})
    recommendation = planner_result.get("recommendation", {})
    statement_preview = recommendation.get("statement_preview", "")

    # Check 1 - approved
    if approval_status != "APPROVED":
        return _build_result(
            success=False,
            request_id=request_id,
            execution_status=current_execution_status or "NOT_STARTED",
            message=f"Request {request_id} is not approved. Current approval_status = {approval_status}",
            request_record=request_record,
            statement_preview=statement_preview
        )

    # Check 2 - already completed
    if current_execution_status == "COMPLETED":
        return _build_result(
            success=True,
            request_id=request_id,
            execution_status="COMPLETED",
            message=f"Request {request_id} already marked as COMPLETED.",
            request_record=request_record,
            statement_preview=statement_preview
        )

    # Check 3 - policy allowed
    if not policy_result.get("allowed", False):
        update_execution_status(request_id, "BLOCKED")
        return _build_result(
            success=False,
            request_id=request_id,
            execution_status="BLOCKED",
            message=f"Request {request_id} is blocked by policy.",
            request_record=request_record,
            statement_preview=statement_preview
        )

    # Check 3b - execution_enabled flag
    if not policy_result.get("execution_enabled", False):
        update_execution_status(request_id, "BLOCKED")
        return _build_result(
            success=False,
            request_id=request_id,
            execution_status="BLOCKED",
            message=(
                f"Request {request_id} is approved but execution is disabled by policy. "
                f"Set execution_enabled=True in execution_policy.py to allow real execution."
            ),
            request_record=request_record,
            statement_preview=statement_preview
        )

    # Check 4 - statement preview present
    if not statement_preview:
        update_execution_status(request_id, "FAILED")
        return _build_result(
            success=False,
            request_id=request_id,
            execution_status="FAILED",
            message=f"Request {request_id} has no reviewed statement preview.",
            request_record=request_record,
            statement_preview=statement_preview
        )

    # ------------------------------------------------------------
    # Safe dry-run path
    # ------------------------------------------------------------
    if dry_run:
        verification_result = _basic_verification_from_request(request_record)
        update_execution_status(request_id, "DRY_RUN_COMPLETED")

        refreshed_record = get_approval_request(request_id)

        return _build_result(
            success=True,
            request_id=request_id,
            execution_status="DRY_RUN_COMPLETED",
            message=(
                f"Dry run completed for {request_id}. "
                f"No database change was executed."
            ),
            request_record=refreshed_record,
            statement_preview=statement_preview,
            verification_result=verification_result
        )

    # ------------------------------------------------------------
    # Live execution path requires enterprise-approved callback
    # ------------------------------------------------------------
    if executor_callback is None:
        update_execution_status(request_id, "READY_FOR_MANUAL_EXECUTION")

        refreshed_record = get_approval_request(request_id)

        return _build_result(
            success=False,
            request_id=request_id,
            execution_status="READY_FOR_MANUAL_EXECUTION",
            message=(
                f"Request {request_id} is approved, but live execution is not available "
                f"from this workflow. Use an approved internal execution method."
            ),
            request_record=refreshed_record,
            statement_preview=statement_preview
        )

    # ------------------------------------------------------------
    # Controlled external execution hook
    # ------------------------------------------------------------
    try:
        callback_result = executor_callback(conn, request_record, statement_preview)

        if callback_result.get("success"):
            update_execution_status(request_id, "COMPLETED")
            refreshed_record = get_approval_request(request_id)

            verification_result = callback_result.get("verification_result", {})
            return _build_result(
                success=True,
                request_id=request_id,
                execution_status="COMPLETED",
                message=callback_result.get("message", f"Execution completed for {request_id}."),
                request_record=refreshed_record,
                statement_preview=statement_preview,
                verification_result=verification_result
            )

        update_execution_status(request_id, "FAILED")
        refreshed_record = get_approval_request(request_id)

        return _build_result(
            success=False,
            request_id=request_id,
            execution_status="FAILED",
            message=callback_result.get("message", f"Execution failed for {request_id}."),
            request_record=refreshed_record,
            statement_preview=statement_preview,
            verification_result=callback_result.get("verification_result", {})
        )

    except Exception as exc:
        update_execution_status(request_id, "FAILED")
        refreshed_record = get_approval_request(request_id)

        return _build_result(
            success=False,
            request_id=request_id,
            execution_status="FAILED",
            message=f"Execution callback error for {request_id}: {str(exc)}",
            request_record=refreshed_record,
            statement_preview=statement_preview
        )


# ─────────────────────────────────────────────────────────────────────────────
# Real Oracle executor callback
# Pass this into execute_approved_change_request() as executor_callback=
# ─────────────────────────────────────────────────────────────────────────────

def oracle_alter_tablespace_callback(
    conn,
    request_record: Dict[str, Any],
    statement_preview: str
) -> Dict[str, Any]:
    """
    Real execution callback that fires ALTER TABLESPACE ... ADD DATAFILE
    against the live Oracle database.

    Parameters
    ----------
    conn : oracledb.Connection
        Live Oracle connection (opened and closed by the caller in app.py)
    request_record : dict
        Full approved request record from approval_store
    statement_preview : str
        The ALTER TABLESPACE SQL to execute

    Returns
    -------
    dict with keys: success, message, verification_result
    """
    planner_result = request_record.get("planner_result", {})
    tablespace_name = planner_result.get("tablespace_name", "UNKNOWN")
    recommendation = planner_result.get("recommendation", {})
    recommended_file_path = recommendation.get("recommended_file_path", "")

    # ── Step 1: Execute the ALTER TABLESPACE ──────────────────────────────
    cursor = conn.cursor()
    try:
        cursor.execute(statement_preview)
        conn.commit()
    except Exception as exec_err:
        cursor.close()
        return {
            "success": False,
            "message": f"ALTER TABLESPACE failed: {exec_err}",
            "verification_result": {}
        }

    # ── Step 2: Verify the datafile was actually added ────────────────────
    verification_result = {}
    try:
        cursor.execute(
            """
            SELECT file_name, ROUND(bytes / 1073741824, 2) AS size_gb, status
            FROM   dba_data_files
            WHERE  tablespace_name = :ts
            ORDER  BY file_id
            """,
            {"ts": tablespace_name.upper()}
        )
        rows = cursor.fetchall()
        file_list = [
            {"file_name": r[0], "size_gb": r[1], "status": r[2]}
            for r in rows
        ]

        # Check if the new file appears in dba_data_files
        new_file_found = any(
            recommended_file_path.lower() in f["file_name"].lower()
            for f in file_list
        )

        verification_result = {
            "tablespace": tablespace_name,
            "datafiles_after": file_list,
            "new_file_confirmed": new_file_found
        }
    except Exception as verify_err:
        # Execution succeeded even if verification query fails
        verification_result = {
            "warning": f"Verification query failed: {verify_err}",
            "new_file_confirmed": False
        }
    finally:
        cursor.close()

    return {
        "success": True,
        "message": (
            f"ALTER TABLESPACE {tablespace_name} ADD DATAFILE executed "
            f"successfully. New file confirmed: {verification_result.get('new_file_confirmed')}"
        ),
        "verification_result": verification_result
    }
