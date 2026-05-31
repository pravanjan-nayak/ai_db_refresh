from agents.validation_agent import (
    ValidationAgent
)

agent = ValidationAgent()

print("\nDEV")

print(
    agent.validate_schema(
        "DEV",
        "HR"
    )
)

print("\nUAT")

print(
    agent.validate_schema(
        "UAT",
        "HR"
    )
)