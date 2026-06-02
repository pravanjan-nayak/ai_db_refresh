from executors.expdp_executor import run_expdp
from executors.impdp_executor import run_impdp

class ExecutionAgent:

    def execute_refresh(
            self,
            source_db,
            target_db,
            schema):

        export_result = run_expdp(
            "system",
            "password",
            source_db,
            schema,
            f"{schema}.dmp"
        )

        if not export_result["success"]:
            return export_result

        import_result = run_impdp(
            "system",
            "password",
            target_db,
            schema,
            f"{schema}.dmp"
        )

        return import_result