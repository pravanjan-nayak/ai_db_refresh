# workflows/schema_refresh_workflow.py
from agents.expdp_agent import ExpdpAgent
from workflows.schema_refresh import (
    create_schema_refresh_plan
)

from agents.impdp_agent import (
    ImpdpAgent
)

from agents.verification_agent import (
    VerificationAgent
)


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

            # STEP 1
            workflow = (
                create_schema_refresh_plan(
                    source_tns,
                    target_tns,
                    username,
                    password,
                    schema_name
                )
            )

            result["workflow"] = (
                workflow
            )

            # STEP 2
            if workflow["status"] == "FAILED":

                result["errors"].extend(
                    workflow["errors"]
                )

                return result

            # STEP 3
            if workflow.get(
                "approval_required",
                False
            ):

                if not approved:

                    result["errors"].append(
                        "Workflow requires approval."
                    )

                    return result

                workflow[
                    "approval_received"
                ] = True

                workflow[
                    "status"
                ] = "APPROVED"

            # STEP 4
            export_agent = ExpdpAgent()

            export_result = export_agent.export_schema(
                username=username,
                password=password,
                tns_alias=source_tns,
                schema_name=schema_name
            )

            workflow["export_result"] = export_result

            if not export_result["success"]:

                workflow["status"] = "FAILED"

                workflow["errors"].append(
                    "Export failed"
                )

                return {
                    "success": False,
                    "workflow": workflow,
                    "errors": workflow["errors"]
                }


            

            # STEP 5
            import_agent = ImpdpAgent()

            import_result = import_agent.import_schema(
                username=username,
                password=password,
                tns_alias=target_tns,
                schema_name=schema_name
            )


            workflow["import_result"] = import_result

            if not import_result["success"]:

                workflow["status"] = "FAILED"

                workflow["errors"].append(
                    "Import failed"
                )

                return {
                    "success": False,
                     "workflow": workflow,
                     "errors": workflow["errors"]
                 }
            

            # STEP 6
            verifier = (
                VerificationAgent()
            )

            verification = (
                verifier.verify(
                    username,
                    password,
                    source_tns,
                    schema_name
                )
            )

            result[
                "verification"
            ] = verification

            # STEP 7
            workflow[
                "status"
            ] = "COMPLETED"

            result[
                "success"
            ] = True

            return result

        except Exception as e:

            result[
                "errors"
            ].append(
                str(e)
            )

            return result