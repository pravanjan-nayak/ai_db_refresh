# test_workflow_tracker.py

from workflows.workflow_tracker import (
    update_state,
    get_state
)

test_data = {
    "workflow_id": "WF001",
    "status": "RUNNING",
    "schema": "HR"
}

update_state(test_data)

result = get_state()

print(result)