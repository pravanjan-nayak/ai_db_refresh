# test_real_expdp.py

from agents.expdp_agent import (
    ExpdpAgent
)

agent = ExpdpAgent()

result = agent.export_schema(
    username="system",
    password="tiger",
    tns_alias="orclpdb",
    schema_name="HR"
)

print(result)