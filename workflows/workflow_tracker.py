import json
from pathlib import Path

STATE_FILE = Path(
    "state/workflow_state.json"
)

def update_state(data):

    STATE_FILE.parent.mkdir(
        exist_ok=True
    )

    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_state():

    if not STATE_FILE.exists():
        return {}

    with open(STATE_FILE) as f:
        return json.load(f)