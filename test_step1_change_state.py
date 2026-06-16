from state.change_state import ChangeState

state = ChangeState(
    request_id="CR-001",
    request_text="add 10 gb datafile to USERS tablespace",
    action_type="add_datafile",
    target_tablespace="USERS",
    size_gb=10
)

print("SUMMARY:")
print(state.summary())

print("\nDICTIONARY OUTPUT:")
print(state.to_dict())