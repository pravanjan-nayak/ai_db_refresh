from executors.expdp_executor import (
    ExpdpExecutor
)


class ExpdpAgent:

    def export_schema(
        self,
        username,
        password,
        tns_alias,
        schema_name
    ):

        executor = ExpdpExecutor()

        return executor.run(
            username,
            password,
            tns_alias,
            schema_name
        )