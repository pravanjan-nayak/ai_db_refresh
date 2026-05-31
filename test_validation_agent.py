from agents.validation_agent import ValidationAgent

agent = ValidationAgent()

print("\nHR")

print(
    agent.validate_schema("HR")
)

print("\nSYSTEM")

print(
    agent.validate_schema("SYSTEM")
)

print("\nABCXYZ")

print(
    agent.validate_schema("ABCXYZ")
)