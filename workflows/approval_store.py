import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional


STORE_FILE = os.path.join(os.path.dirname(__file__), "approval_store.json")


def _utc_now_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _generate_request_id() -> str:
    return datetime.utcnow().strftime("CR-%Y%m%d-%H%M%S-%f")


def _load_store() -> Dict[str, Any]:
    if not os.path.exists(STORE_FILE):
        return {"requests": {}}

    with open(STORE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_store(data: Dict[str, Any]) -> None:
    with open(STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def create_approval_request(
    request_text: str,
    planner_result: Dict[str, Any],
    policy_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create and persist a new approval request.
    """
    store = _load_store()
    request_id = _generate_request_id()

    record = {
        "request_id": request_id,
        "request_text": request_text,
        "action_type": planner_result.get("action_type"),
        "tablespace_name": planner_result.get("tablespace_name"),
        "requested_size_gb": planner_result.get("requested_size_gb"),
        "planner_result": planner_result,
        "policy_result": policy_result,
        "approval_status": "PENDING",
        "execution_status": "NOT_STARTED",
        "approver": "",
        "approval_time": "",
        "rejection_reason": "",
        "created_at": _utc_now_str(),
        "updated_at": _utc_now_str()
    }

    store["requests"][request_id] = record
    _save_store(store)

    return record


def get_approval_request(request_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch one approval request by request_id.
    """
    store = _load_store()
    return store.get("requests", {}).get(request_id)


def list_approval_requests(status: str = None) -> List[Dict[str, Any]]:
    """
    List all approval requests.
    Optional filter by approval_status:
      PENDING / APPROVED / REJECTED
    """
    store = _load_store()
    requests = list(store.get("requests", {}).values())

    if status:
        status = status.upper()
        requests = [
            req for req in requests
            if (req.get("approval_status") or "").upper() == status
        ]

    # latest first
    requests.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return requests


def approve_request(request_id: str, approver: str = "DBA_USER") -> Dict[str, Any]:
    """
    Mark request as APPROVED.
    """
    store = _load_store()
    requests = store.get("requests", {})

    if request_id not in requests:
        return {
            "success": False,
            "message": f"Request ID not found: {request_id}"
        }

    record = requests[request_id]

    if record.get("approval_status") == "REJECTED":
        return {
            "success": False,
            "message": f"Request {request_id} was already REJECTED and cannot be approved."
        }

    record["approval_status"] = "APPROVED"
    record["approver"] = approver
    record["approval_time"] = _utc_now_str()
    record["updated_at"] = _utc_now_str()

    _save_store(store)

    return {
        "success": True,
        "message": f"Request {request_id} approved successfully.",
        "record": record
    }


def reject_request(
    request_id: str,
    approver: str = "DBA_USER",
    reason: str = ""
) -> Dict[str, Any]:
    """
    Mark request as REJECTED.
    """
    store = _load_store()
    requests = store.get("requests", {})

    if request_id not in requests:
        return {
            "success": False,
            "message": f"Request ID not found: {request_id}"
        }

    record = requests[request_id]

    if record.get("approval_status") == "APPROVED":
        return {
            "success": False,
            "message": f"Request {request_id} was already APPROVED and cannot be rejected."
        }

    record["approval_status"] = "REJECTED"
    record["approver"] = approver
    record["approval_time"] = _utc_now_str()
    record["rejection_reason"] = reason or "No reason provided."
    record["updated_at"] = _utc_now_str()

    _save_store(store)

    return {
        "success": True,
        "message": f"Request {request_id} rejected successfully.",
        "record": record
    }


def update_execution_status(request_id: str, execution_status: str) -> Dict[str, Any]:
    """
    Update execution status later after execution hook is added.
    """
    store = _load_store()
    requests = store.get("requests", {})

    if request_id not in requests:
        return {
            "success": False,
            "message": f"Request ID not found: {request_id}"
        }

    record = requests[request_id]
    record["execution_status"] = execution_status
    record["updated_at"] = _utc_now_str()

    _save_store(store)

    return {
        "success": True,
        "message": f"Execution status updated for {request_id}.",
        "record": record
    }