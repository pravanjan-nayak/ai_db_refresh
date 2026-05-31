class DropSchemaAgent:

    def generate_drop_script(
        self,
        schema_name
    ):

        schema_name = schema_name.upper()

        return (
            f"DROP USER {schema_name} CASCADE;"
        )