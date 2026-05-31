from typing import TypedDict
from typing import List
from typing import Optional


class AgentState(TypedDict):

    user_question: str

    workflow: Optional[str]

    current_step: Optional[str]

    completed_steps: List[str]

    pending_steps: List[str]

    result: Optional[str]

    errors: List[str]