import os
from workflows.change_request_workflow import process_add_datafile_change_request


class MockCursor:
    def __init__(self, working_dir):
        self.working_dir = working_dir
        self.last_query = ""
        self.last_params = {}

    def execute(self, query, params=None):
        self.last_query = query.lower()
        self.last_params = params or {}

    def fetchone(self):
        if "from dba_tablespaces" in self.last_query:
            return ("PERMANENT",)
        return None

    def fetchall(self):
        if "from dba_data_files" in self.last_query:
            sample_file = os.path.join(self.working_dir, "users_01.dbf")
            return [
                (sample_file, 5 * 1024 * 1024 * 1024)
            ]
        return []

    def close(self):
        pass


class MockConnection:
    def __init__(self, working_dir):
        self.working_dir = working_dir

    def cursor(self):
        return MockCursor(self.working_dir)


conn = MockConnection(os.getcwd())

result = process_add_datafile_change_request(
    conn=conn,
    user_text="add 10 gb datafile to USERS tablespace"
)

print("STEP 6 WORKFLOW RESULT")
print("-" * 60)
print(f"success: {result['success']}")
print(f"workflow_type: {result['workflow_type']}")
print(f"action_type: {result['action_type']}")
print(f"status: {result['status']}")
print(f"request_id: {result['request_id']}")

print("\nPLANNER RESULT")
print("-" * 60)
print(f"planner_success: {result['planner_result'].get('success')}")
print(f"tablespace_name: {result['planner_result'].get('tablespace_name')}")
print(f"requested_size_gb: {result['planner_result'].get('requested_size_gb')}")

print("\nPOLICY RESULT")
print("-" * 60)
print(f"allowed: {result['policy_result'].get('allowed')}")
print(f"approval_required: {result['policy_result'].get('approval_required')}")
print(f"execution_enabled: {result['policy_result'].get('execution_enabled')}")
print(f"risk_level: {result['policy_result'].get('risk_level')}")

print("\nAPPROVAL RECORD")
print("-" * 60)
approval_record = result.get("approval_record", {})
print(f"approval_status: {approval_record.get('approval_status')}")
print(f"execution_status: {approval_record.get('execution_status')}")
print(f"created_at: {approval_record.get('created_at')}")

print("\nERRORS")
print("-" * 60)
print(result["errors"])