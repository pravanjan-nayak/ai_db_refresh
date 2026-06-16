import os

from tools.change_tool import (
    submit_add_datafile_request,
    get_change_request_status,
    list_pending_change_requests,
    approve_change_request
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

# Step 1 - submit request
submit_result = submit_add_datafile_request(
    conn=conn,
    user_text="add 10 gb datafile to USERS tablespace"
)

print("STEP 7 SUBMIT RESULT")
print("-" * 60)
print(f"success: {submit_result['success']}")
print(f"status: {submit_result['status']}")
print(f"request_id: {submit_result['request_id']}")

request_id = submit_result["request_id"]

# Step 2 - get status
status_result = get_change_request_status(request_id)

print("\nSTEP 7 STATUS RESULT")
print("-" * 60)
print(f"success: {status_result['success']}")
print(f"message: {status_result['message']}")
print(f"approval_status: {status_result['record'].get('approval_status')}")
