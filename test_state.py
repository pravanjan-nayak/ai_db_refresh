from state.agent_state import AgentState


state: AgentState = {
    "user_question": "Refresh HR schema",
    "workflow": "schema_refresh",
    "current_step": "validate_source",
    "completed_steps": [],
    "pending_steps": [
        "validate_source",
        "export_schema",
        "import_schema",
        "validate_target"
    ],
    "result": None,
    "errors": []
}

print(state)