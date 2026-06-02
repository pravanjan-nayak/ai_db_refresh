from agents.dynamic_validation_agent import (
    DynamicValidationAgent
)

agent = DynamicValidationAgent()

result = agent.validate_schema(
    username="system",
    password="tiger",
    tns_alias="orclpdb",
    schema_name="HR"
)

print(result)