from agents.verification_agent import (
    VerificationAgent
)

agent = VerificationAgent()

result = agent.verify(
    username="system",
    password="tiger",
    tns_alias="orclpdb",
    schema_name="HR"
)

print(result)