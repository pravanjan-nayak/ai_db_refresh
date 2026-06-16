from typing import Dict, Any, Optional

from workflows.change_planner import plan_add_datafile_request
from workflows.execution_policy import evaluate_add_datafile_policy
from workflows.approval_store import create_approval_request


def process_add_datafile_change_request(
    conn,
    user_text: str,
    policy_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    End-to-end workflow for add datafile request.

    Steps:
    1. Planner parses and validates request
    2. Policy evaluates whether request is allowed
    3. If allowed, approval request is created
    4. Final structured result is returned

    This step does NOT execute the SQL.
    It only prepares the request for approval.
    """
    result = {
        "success": False,
        "workflow_type": "change_request",
        "action_type": "add_datafile",
        "request_text": user_text,
        "planner_result": {},
        "policy_result": {},
        "approval_record": {},
        "request_id": "",
        "status": "FAILED",
        "errors": []
    }

    # Step 1 - planner
    planner_result = plan_add_datafile_request(
        conn=conn,
        user_text=user_text
    )
    result["planner_result"] = planner_result

    if not planner_result.get("success"):
        result["status"] = "PLANNER_FAILED"
        result["errors"].extend(planner_result.get("errors", []))
        return result

    # Step 2 - policy
    policy_result = evaluate_add_datafile_policy(
        planner_result=planner_result,
        policy_config=policy_config
    )
    result["policy_result"] = policy_result

    if not policy_result.get("allowed"):
        result["status"] = "BLOCKED_BY_POLICY"
        result["errors"].extend(policy_result.get("policy_messages", []))
        return result

    # Step 3 - create approval request
    approval_record = create_approval_request(
        request_text=user_text,
        planner_result=planner_result,
        policy_result=policy_result
    )

    result["approval_record"] = approval_record
    result["request_id"] = approval_record.get("request_id", "")

    # Step 4 - final status
    if policy_result.get("approval_required"):
        result["status"] = "PENDING_APPROVAL"
    else:
        result["status"] = "READY_FOR_EXECUTION"

    result["success"] = True
    return result