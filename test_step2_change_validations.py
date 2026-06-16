import os
from db.change_validations import recommend_add_datafile


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
            # Simulate permanent tablespace
            return ("PERMANENT",)
        return None

    def fetchall(self):
        if "from dba_data_files" in self.last_query:
            # Use current working directory so directory check passes
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

result = recommend_add_datafile(
    conn=conn,
    tablespace_name="USERS",
    requested_size_gb=2
)

print("STEP 2 RESULT")
print("-" * 60)

for key, value in result.items():
    print(f"{key}: {value}")