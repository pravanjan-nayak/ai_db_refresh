from typing import Dict, Any


DEFAULT_POLICY = {
    "allowed_actions": ["add_datafile"],
    "max_request_size_gb": 20,
    "approval_required": True,
    "execution_enabled": False,   # keep False for now
    "allowed_tablespaces": [],    # empty means allow any permanent TS
    "blocked_tablespaces": ["SYSTEM", "SYSAUX"],
    "environment_name": "UAT"
}


def evaluate_add_datafile_policy(
    planner_result: Dict[str, Any],
    policy_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Evaluate whether add-datafile request is allowed by policy.
    Input should be the output of plan_add_datafile_request().
    """
    config = dict(DEFAULT_POLICY)
    if policy_config:
        config.update(policy_config)

    result = {
        "allowed": False,
        "approval_required": config["approval_required"],
        "execution_enabled": config["execution_enabled"],
        "risk_level": "UNKNOWN",
        "policy_messages": [],
        "policy_checks": [],
        "environment_name": config["environment_name"]
    }

    if not planner_result:
        result["policy_messages"].append("Planner result is empty.")
        result["policy_checks"].append({
            "name": "planner_result_present",
            "status": "FAIL",
            "details": "Planner result is empty."
        })
        return result

    action_type = planner_result.get("action_type")
    tablespace_name = (planner_result.get("tablespace_name") or "").upper()
    requested_size_gb = planner_result.get("requested_size_gb")
    recommendation = planner_result.get("recommendation", {})
    planner_success = planner_result.get("success", False)

    # Check 1 - planner success
    result["policy_checks"].append({
        "name": "planner_success",
        "status": "PASS" if planner_success else "FAIL",
        "details": f"Planner success = {planner_success}"
    })

    if not planner_success:
        result["policy_messages"].append("Planner failed. Request cannot proceed.")
        result["risk_level"] = "HIGH"
        return result

    # Check 2 - action allowed
    action_allowed = action_type in config["allowed_actions"]
    result["policy_checks"].append({
        "name": "action_allowed",
        "status": "PASS" if action_allowed else "FAIL",
        "details": f"Action '{action_type}' allowed actions = {config['allowed_actions']}"
    })

    if not action_allowed:
        result["policy_messages"].append(
            f"Action '{action_type}' is not allowed by policy."
        )
        result["risk_level"] = "HIGH"
        return result

    # Check 3 - blocked tablespaces
    is_blocked_ts = tablespace_name in [ts.upper() for ts in config["blocked_tablespaces"]]
    result["policy_checks"].append({
        "name": "blocked_tablespace_check",
        "status": "FAIL" if is_blocked_ts else "PASS",
        "details": f"Tablespace = {tablespace_name}"
    })

    if is_blocked_ts:
        result["policy_messages"].append(
            f"Tablespace '{tablespace_name}' is blocked by policy."
        )
        result["risk_level"] = "HIGH"
        return result

    # Check 4 - allowed tablespaces (optional whitelist)
    allowed_tablespaces = [ts.upper() for ts in config["allowed_tablespaces"]]
    if allowed_tablespaces:
        ts_allowed = tablespace_name in allowed_tablespaces
        result["policy_checks"].append({
            "name": "allowed_tablespace_check",
            "status": "PASS" if ts_allowed else "FAIL",
            "details": f"Tablespace = {tablespace_name}, allowed list = {allowed_tablespaces}"
        })

        if not ts_allowed:
            result["policy_messages"].append(
                f"Tablespace '{tablespace_name}' is not in allowed tablespace list."
            )
            result["risk_level"] = "HIGH"
            return result
    else:
        result["policy_checks"].append({
            "name": "allowed_tablespace_check",
            "status": "PASS",
            "details": "No tablespace whitelist configured."
        })

    # Check 5 - size threshold
    max_request_size_gb = config["max_request_size_gb"]
    size_ok = isinstance(requested_size_gb, int) and requested_size_gb <= max_request_size_gb
    result["policy_checks"].append({
        "name": "size_threshold_check",
        "status": "PASS" if size_ok else "FAIL",
        "details": f"Requested size = {requested_size_gb} GB, max allowed = {max_request_size_gb} GB"
    })

    if not size_ok:
        result["policy_messages"].append(
            f"Requested size {requested_size_gb} GB exceeds max allowed {max_request_size_gb} GB."
        )
        result["risk_level"] = "HIGH"
        return result

    # Check 6 - recommendation validity
    recommendation_valid = recommendation.get("valid", False)
    result["policy_checks"].append({
        "name": "recommendation_valid",
        "status": "PASS" if recommendation_valid else "FAIL",
        "details": f"Recommendation valid = {recommendation_valid}"
    })

    if not recommendation_valid:
        result["policy_messages"].append(
            "Recommendation/validation result is not valid."
        )
        result["risk_level"] = "HIGH"
        return result

    sufficient_space = recommendation.get("sufficient_space", False)
    result["policy_checks"].append({
        "name": "sufficient_space_check",
        "status": "PASS" if sufficient_space else "FAIL",
        "details": f"Sufficient space = {sufficient_space}"
    })

    if not sufficient_space:
        result["policy_messages"].append("Insufficient space as per recommendation.")
        result["risk_level"] = "HIGH"
        return result

    # Final policy result
    result["allowed"] = True

    # Risk classification
    if requested_size_gb <= 5:
        result["risk_level"] = "LOW"
    elif requested_size_gb <= 10:
        result["risk_level"] = "MEDIUM"
    else:
        result["risk_level"] = "HIGH"

    result["policy_messages"].append("Request is allowed by current policy.")
    if result["approval_required"]:
        result["policy_messages"].append("Approval is required before execution.")

    if result["execution_enabled"]:
        result["policy_messages"].append("Execution is enabled by policy.")
    else:
        result["policy_messages"].append("Execution is currently disabled by policy.")

    return result