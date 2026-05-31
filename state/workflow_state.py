from typing import TypedDict
from typing import List
from typing import Optional


class WorkflowState(TypedDict):

    workflow_name: str

    risk_level: str

    status: str

    current_step: Optional[str]

    completed_steps: List[str]

    pending_steps: List[str]

    approval_required: bool

    approval_received: bool

    result: Optional[str]

    errors: List[str]