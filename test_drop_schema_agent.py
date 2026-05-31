from agents.drop_schema_agent import (
    DropSchemaAgent
)

agent = DropSchemaAgent()

print(
    agent.generate_drop_script(
        "HR"
    )
)