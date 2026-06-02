# test_schema_refresh_workflow.py

from workflows.schema_refresh import (
    create_schema_refresh_plan
)

from agents.approval_agent import (
    requires_approval
)

from agents.verification_agent import (
    VerificationAgent
)


def mock_export(schema_name):

    print(
        f"[EXPORT] Exporting schema {schema_name}"
    )

    return {
        "success": True,
        "dump_file": f"{schema_name}.dmp"
    }


def mock_import(schema_name):

    print(
        f"[IMPORT] Importing schema {schema_name}"
    )

    return {
        "success": True
    }


def run_workflow():

    print("\n=== STEP 1 : CREATE REFRESH PLAN ===\n")

    workflow = create_schema_refresh_plan(
        source_tns="orclpdb",
        target_tns="uatagent",
        username="system",
        password="tiger",
        schema_name="HR"
    )

    print(
        f"Status: {workflow['status']}"
    )

    print(
        f"Approval Required: "
        f"{workflow['approval_required']}"
    )

    print(
        f"Execution Plan: "
        f"{workflow['execution_plan']}"
    )

    print("\n=== STEP 2 : APPROVAL CHECK ===\n")

    if workflow["approval_required"]:

        print(
            "Auto-approving for test..."
        )

        workflow[
            "approval_received"
        ] = True

    print("\n=== STEP 3 : MOCK EXPORT ===\n")

    export_result = mock_export(
        workflow["schema_name"]
    )

    if not export_result["success"]:

        print(
            "Export failed."
        )

        return

    print(
        export_result
    )

    print("\n=== STEP 4 : MOCK IMPORT ===\n")

    import_result = mock_import(
        workflow["schema_name"]
    )

    if not import_result["success"]:

        print(
            "Import failed."
        )

        return

    print(
        import_result
    )

    print("\n=== STEP 5 : VERIFY REFRESH ===\n")

    verifier = VerificationAgent()

    verification_result = verifier.verify(
        username="system",
        password="tiger",
        tns_alias="orclpdb",
        schema_name="HR"
    )

    print(
        verification_result
    )

    print("\n=== STEP 6 : FINAL REPORT ===\n")

    print(
        workflow["report"]
    )

    print(
        "\nWORKFLOW COMPLETED SUCCESSFULLY"
    )


if __name__ == "__main__":

    run_workflow()