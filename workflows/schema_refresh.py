from agents.validation_agent import ValidationAgent
from workflow_engine import start_workflow

from agents.expdp_agent import ExpdpAgent
from agents.impdp_agent import ImpdpAgent
from agents.drop_schema_agent import DropSchemaAgent


def create_schema_refresh_plan(
    source_env,
    target_env,
    schema_name
):

    workflow = start_workflow(
        "schema_refresh"
    )

    validator = ValidationAgent()

    expdp_agent = ExpdpAgent()

    impdp_agent = ImpdpAgent()

    drop_agent = DropSchemaAgent()

    source_schema = validator.validate_schema(
        source_env,
        schema_name
    )

    target_schema = validator.validate_schema(
        target_env,
        schema_name
    )

    workflow["source_env"] = source_env

    workflow["target_env"] = target_env

    workflow["schema_name"] = schema_name

    workflow["source_schema"] = source_schema

    workflow["target_schema"] = target_schema

    if not source_schema["exists"]:

        workflow["status"] = "FAILED"

        workflow["errors"].append(
            f"Source schema {schema_name} does not exist"
        )

        return workflow

    if target_schema["exists"]:

        workflow["drop_required"] = True

        workflow["approval_message"] = (
            f"Target schema {schema_name} already exists. "
            f"Drop and refresh?"
        )

        workflow["drop_script"] = (
            drop_agent.generate_drop_script(
                schema_name
            )
        )

    else:

        workflow["drop_required"] = False

    steps = [

        "validate_source",

        "validate_target"

    ]

    if target_schema["exists"]:

        steps.append(
            "drop_target_schema"
        )

    steps.extend([

        "export_schema",

        "import_schema",

        "validate_refresh"

    ])

    workflow["execution_plan"] = steps

    workflow["expdp_command"] = (
        expdp_agent.generate_command(
            schema_name
        )
    )

    workflow["impdp_command"] = (
        impdp_agent.generate_command(
            schema_name
        )
    )

    return workflow