RISK_MATRIX = {

    "health_check": "LOW",

    "active_sessions": "LOW",

    "database_status": "LOW",

    "backup_validation": "MEDIUM",

    "generate_expdp": "MEDIUM",

    "kill_session": "HIGH",

    "schema_refresh": "CRITICAL",

    "rman_clone": "CRITICAL",

    "drop_schema": "CRITICAL"
}


def get_risk_level(workflow_name):

    return RISK_MATRIX.get(
        workflow_name,
        "MEDIUM"
    )