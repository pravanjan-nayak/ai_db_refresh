import os
from workflows.change_planner import plan_add_datafile_request
from workflows.execution_policy import evaluate_add_datafile_policy


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

planner_result = plan_add_datafile_request(
    conn=conn,
    user_text="add 10 gb datafile to USERS tablespace"
)

policy_result = evaluate_add_datafile_policy(planner_result)

print("STEP 4 POLICY RESULT")
print("-" * 60)

for key, value in policy_result.items():
    print(f"{key}: {value}")