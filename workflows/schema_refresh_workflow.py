# workflows/schema_refresh_workflow.py

from workflows.schema_refresh import create_schema_refresh_plan

from executors.expdp_executor import ExpdpExecutor
from executors.impdp_executor import ImpdpExecutor
from agents.verification_agent import VerificationAgent


class SchemaRefreshWorkflow:

    def execute(
        self,
        source_tns,
        target_tns,
        username,
        password,
        schema_name,
        approved=False
    ):

        result = {
            "success": False,
            "workflow": None,
            "verification": None,
            "errors": []
        }

        try:

            # STEP 1: PLAN
            workflow = create_schema_refresh_plan(
                source_tns,
                target_tns,
                username,
                password,
                schema_name
            )

            result["workflow"] = workflow

            if workflow["status"] == "FAILED":
                result["errors"].extend(workflow["errors"])
                return result

            # STEP 2: APPROVAL CHECK
            if workflow.get("approval_required", False):

                if not approved:
                    result["errors"].append("Workflow requires approval.")
                    return result

                workflow["approval_received"] = True
                workflow["status"] = "APPROVED"

            # STEP 3: EXPORT (EXECUTOR LAYER)
            exp_executor = ExpdpExecutor()

            export_result = exp_executor.execute(
                username=username,
                password=password,
                tns_alias=source_tns,
                schema_name=schema_name
            )

            workflow["export_result"] = export_result

            if not export_result["success"]:
                workflow["status"] = "FAILED"
                workflow["errors"].append("Export failed")

                result["workflow"] = workflow
                result["errors"] = workflow["errors"]
                return result

            # STEP 4: IMPORT (EXECUTOR LAYER)
            imp_executor = ImpdpExecutor()

            import_result = imp_executor.execute(
                username=username,
                password=password,
                tns_alias=target_tns,
                schema_name=schema_name
            )

            workflow["import_result"] = import_result

            if not import_result["success"]:
                workflow["status"] = "FAILED"
                workflow["errors"].append("Import failed")

                result["workflow"] = workflow
                result["errors"] = workflow["errors"]
                return result

            # STEP 5: VERIFY (AGENT OK HERE)
            verifier = VerificationAgent()

            verification = verifier.verify(
                username,
                password,
                source_tns,
                schema_name
            )

            result["verification"] = verification

            # STEP 6: SUCCESS
            workflow["status"] = "COMPLETED"
            result["workflow"] = workflow
            result["success"] = True

            return result

        except Exception as e:

            result["errors"].append(str(e))
            return result