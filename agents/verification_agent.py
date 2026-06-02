from agents.dynamic_validation_agent import (
    DynamicValidationAgent
)


class VerificationAgent:

    def __init__(self):

        self.validator = (
            DynamicValidationAgent()
        )

    def verify(
        self,
        username,
        password,
        tns_alias,
        schema_name
    ):

        return self.validator.validate_schema(
            username,
            password,
            tns_alias,
            schema_name
        )