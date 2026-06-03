# workflow_engine.py

from agents.risk_agent import get_risk_level
from agents.approval_agent import requires_approval


class WorkflowEngine:

    def create_workflow_state(
        self,
        workflow_name,
        source_tns=None,
        target_tns=None,
        schema_name=None
    ):

        risk_level = get_risk_level(workflow_name)

        state = {
            "workflow_name": workflow_name,

            "source_tns": source_tns,
            "target_tns": target_tns,
            "schema_name": schema_name,

            "risk_level": risk_level,

            "status": "STARTING",

            "current_step": None,

            "completed_steps": [],

            "pending_steps": [],

            "approval_required": requires_approval(risk_level),

            "approval_received": False,

            "result": None,

            "errors": []
        }

        # Decide initial status
        if state["approval_required"]:
            state["status"] = "WAITING_APPROVAL"
        else:
            state["status"] = "READY"

        return state