# test_risk_agent.py

from agents.risk_agent import get_risk_level

print("health_check =", get_risk_level("health_check"))
print("generate_expdp =", get_risk_level("generate_expdp"))
print("schema_refresh =", get_risk_level("schema_refresh"))
print("drop_schema =", get_risk_level("drop_schema"))
print("unknown_workflow =", get_risk_level("unknown_workflow"))