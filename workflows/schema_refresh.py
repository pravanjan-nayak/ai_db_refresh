from agents.risk_agent import (
    get_risk_level
)

from agents.dynamic_validation_agent import (
    DynamicValidationAgent
)

from agents.report_agent import ReportAgent


def create_schema_refresh_plan(
    source_tns,
    target_tns,
    username,
    password,
    schema_name
):

    workflow = {
        "workflow_name": "schema_refresh",
        "status": "STARTING",
        "approval_required": False,
        "approval_received": False,
        "completed_steps": [],
        "pending_steps": [],
        "errors": []
    }

    validator = DynamicValidationAgent()

    # STEP 1: Validate Source DB
    source_schema = validator.validate_schema(
        username,
        password,
        source_tns,
        schema_name
    )

    # STEP 2: Validate Target DB
    target_schema = validator.validate_schema(
        username,
        password,
        target_tns,
        schema_name
    )

    workflow["source_tns"] = source_tns
    workflow["target_tns"] = target_tns
    workflow["schema_name"] = schema_name

    workflow["source_schema"] = source_schema
    workflow["target_schema"] = target_schema

    # STEP 3: Fail fast if source missing
    if not source_schema["exists"]:
        workflow["status"] = "FAILED"
        workflow["errors"].append(
            f"Source schema {schema_name} does not exist in {source_tns}"
        )
        return workflow

    # STEP 4: Risk + Approval logic
    if target_schema["exists"]:
        workflow["drop_required"] = True
        workflow["status"] = "WAITING_APPROVAL"
        workflow["approval_required"] = True
        workflow["approval_message"] = (
            f"Target schema {schema_name} exists in {target_tns}. "
            "Drop and refresh?"
        )
    else:
        workflow["drop_required"] = False
        workflow["status"] = "READY"

    # STEP 5: Execution Plan
    steps = [
        "validate_source",
        "validate_target"
    ]

    if target_schema["exists"]:
        steps.append("drop_target_schema")

    steps.extend([
        "export_schema",
        "import_schema",
        "validate_refresh"
    ])

    workflow["execution_plan"] = steps

    # STEP 6: Commands (can later be improved per environment)
    workflow["expdp_command"] = (
        f"expdp system/{password}@{source_tns} schemas={schema_name} "
        f"directory=DATA_PUMP_DIR dumpfile={schema_name}.dmp logfile={schema_name}_exp.log"
    )

    workflow["impdp_command"] = (
        f"impdp system/{password}@{target_tns} schemas={schema_name} "
        f"directory=DATA_PUMP_DIR dumpfile={schema_name}.dmp logfile={schema_name}_imp.log"
    )
    workflow["risk_level"] = (
    get_risk_level(
        "schema_refresh"
    )
)
    # STEP 7: Generate Report
    report_agent = ReportAgent()
    workflow["report"] = report_agent.generate_report(workflow)

    return workflow