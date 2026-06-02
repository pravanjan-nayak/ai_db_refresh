# test_workflow_chain.py

from agents.risk_agent import get_risk_level
from agents.approval_agent import (
    requires_approval,
    check_user_approval
)

workflow = "schema_refresh"

risk = get_risk_level(workflow)

print("Risk:", risk)

if requires_approval(risk):

    approved = check_user_approval("YES")

    if approved:
        print("Approved")
    else:
        print("Rejected")
else:
    print("No Approval Required")