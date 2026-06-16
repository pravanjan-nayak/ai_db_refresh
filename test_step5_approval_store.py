import os
from workflows.change_planner import plan_add_datafile_request
from workflows.execution_policy import evaluate_add_datafile_policy
from workflows.approval_store import (
    create_approval_request,
    get_approval_request,
    list_approval_requests,
    approve_request
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

# Step 1: planner
planner_result = plan_add_datafile_request(
    conn=conn,
    user_text="add 10 gb datafile to USERS tablespace"
)

# Step 2: policy
policy_result = evaluate_add_datafile_policy(planner_result)

# Step 3: create approval record
record = create_approval_request(
    request_text="add 10 gb datafile to USERS tablespace",
    planner_result=planner_result,
    policy_result=policy_result
)

request_id = record["request_id"]

print("CREATED APPROVAL REQUEST")
print("-" * 60)
print(f"request_id: {request_id}")
print(f"approval_status: {record['approval_status']}")
print(f"execution_status: {record['execution_status']}")
print(f"tablespace_name: {record['tablespace_name']}")
print(f"requested_size_gb: {record['requested_size_gb']}")

# Step 4: read back
fetched = get_approval_request(request_id)

print("\nFETCHED REQUEST")
print("-" * 60)
print(f"request_id: {fetched['request_id']}")
print(f"approval_status: {fetched['approval_status']}")
print(f"created_at: {fetched['created_at']}")

# Step 5: list pending
pending_requests = list_approval_requests(status="PENDING")

print("\nPENDING REQUEST COUNT")
print("-" * 60)
print(len(pending_requests))

# Step 6: approve request
approval_result = approve_request(request_id, approver="Pravanjan")

print("\nAPPROVAL RESULT")
print("-" * 60)
print(approval_result["message"])

# Step 7: read again after approval
fetched_after = get_approval_request(request_id)

print("\nFETCHED AFTER APPROVAL")
print("-" * 60)
print(f"request_id: {fetched_after['request_id']}")
print(f"approval_status: {fetched_after['approval_status']}")
print(f"approver: {fetched_after['approver']}")
print(f"approval_time: {fetched_after['approval_time']}")