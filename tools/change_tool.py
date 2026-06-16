from typing import Dict, Any, Optional, List, Callable

from workflows.change_request_workflow import process_add_datafile_change_request
from workflows.approval_store import (
    get_approval_request,
    list_approval_requests,
    approve_request,
    reject_request
)
from workflows.change_executor import execute_approved_change_request


def submit_add_datafile_request(
    conn,
    user_text: str,
    policy_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Submit add-datafile request through end-to-end workflow.
    Returns planner result + policy result + approval record.
    """
    return process_add_datafile_change_request(
        conn=conn,
        user_text=user_text,
        policy_config=policy_config
    )


def get_change_request_status(request_id: str) -> Dict[str, Any]:
    """
    Get current status of a specific approval/change request.
    """
    record = get_approval_request(request_id)

    if not record:
        return {
            "success": False,
            "message": f"Request ID not found: {request_id}",
            "record": {}
        }

    return {
        "success": True,
        "message": f"Request ID found: {request_id}",
        "record": record
    }


def list_pending_change_requests() -> List[Dict[str, Any]]:
    """
    Return all pending approval requests.
    """
    return list_approval_requests(status="PENDING")


def list_all_change_requests() -> List[Dict[str, Any]]:
    """
    Return all approval requests.
    """
    return list_approval_requests()


def approve_change_request(request_id: str, approver: str = "DBA_USER") -> Dict[str, Any]:
    """
    Approve a pending request.
    """
    return approve_request(request_id=request_id, approver=approver)


def reject_change_request(
    request_id: str,
    approver: str = "DBA_USER",
    reason: str = ""
) -> Dict[str, Any]:
    """
    Reject a pending request.
    """
    return reject_request(
        request_id=request_id,
        approver=approver,
        reason=reason
    )


def execute_change_request(
    request_id: str,
    conn=None,
    dry_run: bool = True,
    executor_callback: Optional[Callable[[Any, Dict[str, Any], str], Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Execute an approved change request through the execution layer.

    Parameters
    ----------
    request_id : str
        Approved request ID
    conn : optional
        DB connection object for future enterprise-approved execution callback
    dry_run : bool
        True = safe simulation only (recommended for current testing)
    executor_callback : callable
        Optional controlled callback for reviewed internal execution flow

    Returns
    -------
    dict
        Structured execution result
    """
    return execute_approved_change_request(
        request_id=request_id,
        conn=conn,
        dry_run=dry_run,
        executor_callback=executor_callback
    )