import os

from tools.change_tool import (
    submit_add_datafile_request,
    approve_change_request,
    execute_change_request,
    get_change_request_status
)


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

# Step 1 - Submit request
submit_result = submit_add_datafile_request(
    conn=conn,
    user_text="add 10 gb datafile to USERS tablespace"
)

request_id = submit_result["request_id"]

print("STEP 11 SUBMIT RESULT")
print("-" * 60)
print(f"success: {submit_result['success']}")
print(f"status: {submit_result['status']}")
print(f"request_id: {request_id}")

# Step 2 - Approve request
approval_result = approve_change_request(
    request_id=request_id,
    approver="Pravanjan"
)

print("\nSTEP 11 APPROVAL RESULT")
print("-" * 60)
print(f"success: {approval_result['success']}")
print(f"message: {approval_result['message']}")

# Step 3 - Execute request in dry-run mode
execution_result = execute_change_request(
    request_id=request_id,
    conn=conn,
    dry_run=True
)

print("\nSTEP 11 EXECUTION RESULT")
print("-" * 60)
print(f"success: {execution_result['success']}")
print(f"request_id: {execution_result['request_id']}")
print(f"execution_status: {execution_result['execution_status']}")
print(f"message: {execution_result['message']}")

print("\nSTEP 11 STATEMENT PREVIEW")
print("-" * 60)
print(execution_result["statement_preview"])

print("\nSTEP 11 VERIFICATION RESULT")
print("-" * 60)
print(execution_result["verification_result"])

# Step 4 - Fetch latest status
status_result = get_change_request_status(request_id)

print("\nSTEP 11 STATUS AFTER EXECUTION")
print("-" * 60)
print(f"success: {status_result['success']}")
print(f"approval_status: {status_result['record'].get('approval_status')}")
print(f"execution_status: {status_result['record'].get('execution_status')}")