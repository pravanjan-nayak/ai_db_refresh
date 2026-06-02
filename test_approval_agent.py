# test_approval_agent.py

from agents.approval_agent import (
    requires_approval,
    check_user_approval
)

print("HIGH:", requires_approval("HIGH"))
print("CRITICAL:", requires_approval("CRITICAL"))
print("LOW:", requires_approval("LOW"))

print("YES:", check_user_approval("YES"))
print("yes:", check_user_approval("yes"))
print("NO:", check_user_approval("NO"))
print("Blank:", check_user_approval(""))