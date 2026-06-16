import os

from tools.change_tool import (
    submit_add_datafile_request,
    approve_change_request
)
from workflows.change_executor import execute_approved_change_request


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

# Step 1 - submit request
submit_result = submit_add_datafile_request(
    conn=conn,
    user_text="add 10 gb datafile to USERS tablespace"
)

request_id = submit_result["request_id"]

print("STEP 10 SUBMIT RESULT")
print("-" * 60)
print(f"success: {submit_result['success']}")
print(f"status: {submit_result['status']}")
print(f"request_id: {request_id}")

# Step 2 - approve request
approval_result = approve_change_request(
    request_id=request_id,
    approver="Pravanjan"
)

print("\nSTEP 10 APPROVAL RESULT")
print("-" * 60)
print(f"success: {approval_result['success']}")
print(f"message: {approval_result['message']}")

# Step 3 - execute dry run
execution_result = execute_approved_change_request(
    request_id=request_id,
    conn=conn,
    dry_run=True
)

print("\nSTEP 10 EXECUTION RESULT")
print("-" * 60)
print(f"success: {execution_result['success']}")
print(f"request_id: {execution_result['request_id']}")
print(f"execution_status: {execution_result['execution_status']}")
print(f"message: {execution_result['message']}")

print("\nSTATEMENT PREVIEW")
print("-" * 60)
print(execution_result["statement_preview"])

print("\nVERIFICATION RESULT")
print("-" * 60)
print(execution_result["verification_result"])
