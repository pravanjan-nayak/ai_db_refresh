import re
from typing import Dict, Any

from db.change_validations import recommend_add_datafile


def _normalize_text(text: str) -> str:
    return (text or "").strip()


def is_add_datafile_request(user_text: str) -> bool:
    """
    Detect whether the request is related to adding/extending a datafile.
    """
    text = _normalize_text(user_text).lower()

    patterns = [
        r"\badd\s+\d+\s*gb\s+datafile\b",
        r"\badd\s+datafile\b",
        r"\bextend\s+tablespace\b",
        r"\bincrease\s+tablespace\b",
        r"\badd\s+\d+\s*gb\s+to\b"
    ]

    return any(re.search(pattern, text) for pattern in patterns)


def extract_size_gb(user_text: str) -> int:
    """
    Extract size in GB from text.
    Example:
        add 10 gb datafile to users tablespace -> 10
    """
    text = _normalize_text(user_text).lower()

    patterns = [
        r"(\d+)\s*gb",
        r"add\s+(\d+)\s+to"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    raise ValueError("Could not extract size in GB from request.")


def extract_tablespace_name(user_text: str) -> str:
    """
    Extract tablespace name from text.
    Supported examples:
        add 10 gb datafile to USERS tablespace
        add datafile to USERS tablespace
        extend tablespace USERS by 10 gb
        increase tablespace USERS
    """
    text = _normalize_text(user_text)

    patterns = [
        r"to\s+([A-Za-z0-9_]+)\s+tablespace",
        r"tablespace\s+([A-Za-z0-9_]+)\b",
        r"for\s+([A-Za-z0-9_]+)\s+tablespace"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()

    raise ValueError("Could not extract tablespace name from request.")


def plan_add_datafile_request(
    conn,
    user_text: str,
    safety_buffer_gb: int = 2,
    autoextend: bool = True,
    next_gb: int = 1,
    maxsize_gb: int = 20
) -> Dict[str, Any]:
    """
    Main planner for add datafile request.
    - reads natural language request
    - extracts tablespace and size
    - calls validation/recommendation logic
    """
    text = _normalize_text(user_text)

    result = {
        "success": False,
        "action_type": "add_datafile",
        "request_text": text,
        "tablespace_name": "",
        "requested_size_gb": None,
        "recommendation": {},
        "status": "FAILED",
        "errors": []
    }

    if not text:
        result["errors"].append("Request text is empty.")
        return result

    if not is_add_datafile_request(text):
        result["errors"].append("Request is not recognized as add datafile request.")
        return result

    try:
        requested_size_gb = extract_size_gb(text)
        tablespace_name = extract_tablespace_name(text)
    except Exception as exc:
        result["errors"].append(str(exc))
        return result

    result["tablespace_name"] = tablespace_name
    result["requested_size_gb"] = requested_size_gb

    recommendation = recommend_add_datafile(
        conn=conn,
        tablespace_name=tablespace_name,
        requested_size_gb=requested_size_gb,
        safety_buffer_gb=safety_buffer_gb,
        autoextend=autoextend,
        next_gb=next_gb,
        maxsize_gb=maxsize_gb
    )

    result["recommendation"] = recommendation

    if recommendation.get("valid"):
        result["success"] = True
        result["status"] = "PLANNED"
    else:
        result["status"] = "VALIDATION_FAILED"
        result["errors"].extend(recommendation.get("errors", []))

    return result
