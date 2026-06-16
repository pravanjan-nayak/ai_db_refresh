from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List


@dataclass
class ChangeState:
    request_id: str
    request_text: str

    action_type: Optional[str] = None
    target_tablespace: Optional[str] = None
    size_gb: Optional[int] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None

    autoextend: bool = True
    next_gb: int = 1
    maxsize_gb: int = 20

    plan: Dict[str, Any] = field(default_factory=dict)
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    policy_result: Dict[str, Any] = field(default_factory=dict)
    approval_status: str = "PENDING"
    execution_status: str = "NOT_STARTED"
    verification_result: Dict[str, Any] = field(default_factory=dict)
    final_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"ChangeState("
            f"request_id={self.request_id}, "
            f"action_type={self.action_type}, "
            f"tablespace={self.target_tablespace}, "
            f"size_gb={self.size_gb}, "
            f"approval_status={self.approval_status}, "
            f"execution_status={self.execution_status}"
            f")"
        )