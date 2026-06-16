import os
import streamlit as st

from workflow_router import detect_change_request_route
from tools.change_tool import (
    submit_add_datafile_request,
    get_change_request_status,
    list_pending_change_requests,
    approve_change_request,
    reject_change_request,
    execute_change_request
)


# ------------------------------------------------------------
# MOCK DATABASE CONNECTION FOR SAFE UI TESTING
# ------------------------------------------------------------
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


def get_demo_connection():
    return MockConnection(os.getcwd())


def get_demo_db_identity():
    """
    Mock DB identity for UI display.
    Later in real app.py this should come from Oracle session.
    """
    return {
        "host_name": os.environ.get("COMPUTERNAME", "WIN-DBSERVER01"),
        "instance_name": "ORCL1",
        "db_name": "ORCL",
        "db_unique_name": "ORCLUAT",
        "service_name": "orclpdb",
        "con_name": "ORCLPDB1",
        "open_mode": "READ WRITE",
        "database_role": "PRIMARY"
    }


# ------------------------------------------------------------
# SESSION STATE INIT
# ------------------------------------------------------------
def init_session_state():
    if "last_change_result" not in st.session_state:
        st.session_state.last_change_result = None

    if "last_request_id" not in st.session_state:
        st.session_state.last_request_id = ""

    if "last_execution_result" not in st.session_state:
        st.session_state.last_execution_result = None


# ------------------------------------------------------------
# UI HELPERS
# ------------------------------------------------------------
def render_check_table(checks):
    if not checks:
        st.info("No checks available.")
        return

    for item in checks:
        status = item.get("status", "")
        name = item.get("name", "")
        details = item.get("details", "")

        if status == "PASS":
            st.success(f"{name}: {details}")
        elif status == "FAIL":
            st.error(f"{name}: {details}")
        else:
            st.write(f"{name}: {details}")


def render_db_identity():
    db_info = get_demo_db_identity()

    st.subheader("Target Database Context")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Host Name:** {db_info.get('host_name')}")
        st.write(f"**Instance Name:** {db_info.get('instance_name')}")
        st.write(f"**DB Name:** {db_info.get('db_name')}")
        st.write(f"**DB Unique Name:** {db_info.get('db_unique_name')}")

    with col2:
        st.write(f"**Service Name:** {db_info.get('service_name')}")
        st.write(f"**PDB / Container Name:** {db_info.get('con_name')}")
        st.write(f"**Open Mode:** {db_info.get('open_mode')}")
        st.write(f"**Database Role:** {db_info.get('database_role')}")

    st.info(
        f"Please verify the execution target before approval/execution: "
        f"{db_info.get('db_name')} / {db_info.get('instance_name')} / {db_info.get('service_name')}"
    )


def render_execution_result(execution_result):
    if not execution_result:
        return

    db_info = get_demo_db_identity()

    st.subheader("Execution Result")

    st.write(f"**Success:** {execution_result.get('success')}")
    st.write(f"**Request ID:** {execution_result.get('request_id')}")
    st.write(f"**Execution Status:** {execution_result.get('execution_status')}")
    st.write(f"**Message:** {execution_result.get('message')}")

    st.write("**Execution Target Database**")
    st.write(
        f"- DB Name: {db_info.get('db_name')}  \n"
        f"- Instance Name: {db_info.get('instance_name')}  \n"
        f"- Service Name: {db_info.get('service_name')}  \n"
        f"- PDB / Container Name: {db_info.get('con_name')}"
    )

    statement_preview = execution_result.get("statement_preview", "")
    if statement_preview:
        st.write("**Statement Preview Used**")
        st.code(statement_preview, language="sql")

        st.write("**Running Statement Context**")
        st.code(
            f"-- Target DB: {db_info.get('db_name')} | "
            f"Instance: {db_info.get('instance_name')} | "
            f"Service: {db_info.get('service_name')}\n"
            f"{statement_preview}",
            language="sql"
        )

    verification_result = execution_result.get("verification_result", {})
    if verification_result:
        st.write("**Verification Result**")
        st.json(verification_result)

    exec_status = execution_result.get("execution_status", "")
    if exec_status == "READY_FOR_MANUAL_EXECUTION":
        st.warning(
            "This request is approved and ready for controlled execution through your internal reviewed process."
        )


def render_recommendation(result):
    planner_result = result.get("planner_result", {})
    recommendation = planner_result.get("recommendation", {})
    policy_result = result.get("policy_result", {})
    approval_record = result.get("approval_record", {})
    request_id = result.get("request_id", "")

    st.subheader("Change Request Summary")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Workflow Type:** {result.get('workflow_type')}")
        st.write(f"**Action Type:** {result.get('action_type')}")
        st.write(f"**Request ID:** {request_id}")
        st.write(f"**Status:** {result.get('status')}")

    with col2:
        st.write(f"**Tablespace:** {planner_result.get('tablespace_name')}")
        st.write(f"**Requested Size (GB):** {planner_result.get('requested_size_gb')}")
        st.write(f"**Approval Status:** {approval_record.get('approval_status')}")
        st.write(f"**Execution Status:** {approval_record.get('execution_status')}")

    st.markdown("---")

    render_db_identity()

    st.markdown("---")

    st.subheader("Recommendation")
    st.write(f"**Storage Type:** {recommendation.get('storage_type')}")
    st.write(f"**Recommended Directory:** {recommendation.get('recommended_directory')}")
    st.write(f"**Recommended File Name:** {recommendation.get('recommended_file_name')}")
    st.write(f"**Recommended File Path:** {recommendation.get('recommended_file_path')}")
    st.write(f"**Sufficient Space:** {recommendation.get('sufficient_space')}")

    drive_space = recommendation.get("drive_space", {})
    if drive_space:
        st.write("**Drive Space**")
        st.write(f"- Drive Root: {drive_space.get('drive_root')}")
        st.write(f"- Total GB: {drive_space.get('total_gb')}")
        st.write(f"- Used GB: {drive_space.get('used_gb')}")
        st.write(f"- Free GB: {drive_space.get('free_gb')}")

    statement_preview = recommendation.get("statement_preview", "")
    if statement_preview:
        st.write("**Statement Preview**")
        st.code(statement_preview, language="sql")

        db_info = get_demo_db_identity()
        st.write("**Statement + Target DB Context**")
        st.code(
            f"-- Target DB: {db_info.get('db_name')} | "
            f"Instance: {db_info.get('instance_name')} | "
            f"Service: {db_info.get('service_name')}\n"
            f"{statement_preview}",
            language="sql"
        )

    st.markdown("---")

    st.subheader("Validation Checks")
    render_check_table(recommendation.get("checks", []))

    st.markdown("---")

    st.subheader("Policy Result")
    st.write(f"**Allowed:** {policy_result.get('allowed')}")
    st.write(f"**Approval Required:** {policy_result.get('approval_required')}")
    st.write(f"**Execution Enabled:** {policy_result.get('execution_enabled')}")
    st.write(f"**Risk Level:** {policy_result.get('risk_level')}")
    st.write(f"**Environment:** {policy_result.get('environment_name')}")

    messages = policy_result.get("policy_messages", [])
    if messages:
        st.write("**Policy Messages**")
        for msg in messages:
            st.write(f"- {msg}")

    st.markdown("---")
    st.subheader("Approval / Execution Actions")

    if not request_id:
        st.warning("No request ID found, so actions are not available.")
        return

    latest_status_result = get_change_request_status(request_id)
    current_record = latest_status_result.get("record", {}) if latest_status_result.get("success") else {}

    current_approval_status = current_record.get(
        "approval_status",
        approval_record.get("approval_status", "")
    )
    current_execution_status = current_record.get(
        "execution_status",
        approval_record.get("execution_status", "")
    )

    st.write(f"**Current Approval Status:** {current_approval_status}")
    st.write(f"**Current Execution Status:** {current_execution_status}")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Approve Request", key=f"approve_{request_id}"):
            approval_result = approve_change_request(
                request_id=request_id,
                approver="Pravanjan"
            )
            if approval_result.get("success"):
                st.success(approval_result.get("message"))
            else:
                st.error(approval_result.get("message"))
            st.rerun()

    with col2:
        if st.button("Reject Request", key=f"reject_{request_id}"):
            rejection_result = reject_change_request(
                request_id=request_id,
                approver="Pravanjan",
                reason="Rejected during demo review."
            )
            if rejection_result.get("success"):
                st.success(rejection_result.get("message"))
            else:
                st.error(rejection_result.get("message"))
            st.rerun()

    with col3:
        execute_disabled = current_approval_status != "APPROVED"

        if st.button(
            "Send to Controlled Execution",
            key=f"execute_{request_id}",
            disabled=execute_disabled
        ):
            conn = get_demo_connection()
            exec_result = execute_change_request(
                request_id=request_id,
                conn=conn,
                dry_run=False
            )
            st.session_state.last_execution_result = exec_result

            exec_status = exec_result.get("execution_status", "")

            if exec_status == "READY_FOR_MANUAL_EXECUTION":
                st.warning(exec_result.get("message"))
            elif exec_result.get("success"):
                st.success(exec_result.get("message"))
            else:
                st.error(exec_result.get("message"))

            st.rerun()

    if current_approval_status != "APPROVED":
        st.info("Execution button will be enabled only after approval.")

    st.info("This demo now prepares the approved request for controlled execution handoff.")


def render_pending_requests():
    st.subheader("Pending Change Requests")

    pending = list_pending_change_requests()

    if not pending:
        st.info("No pending requests found.")
        return

    for item in pending:
        with st.expander(
            f"{item.get('request_id')} | {item.get('tablespace_name')} | {item.get('requested_size_gb')} GB"
        ):
            st.write(f"**Request Text:** {item.get('request_text')}")
            st.write(f"**Approval Status:** {item.get('approval_status')}")
            st.write(f"**Execution Status:** {item.get('execution_status')}")
            st.write(f"**Created At:** {item.get('created_at')}")
            st.write(f"**Approver:** {item.get('approver')}")


# ------------------------------------------------------------
# MAIN APP
# ------------------------------------------------------------
def main():
    st.set_page_config(page_title="Add Datafile Change Request Demo", layout="wide")
    init_session_state()

    st.title("Oracle AI DBA - Add Datafile Change Request Demo")
    st.write("This demo validates recommendation, approval, and controlled execution handoff workflow.")

    user_text = st.text_input(
        "Enter request",
        value="add 10 gb datafile to USERS tablespace"
    )

    if st.button("Submit Request"):
        route_result = detect_change_request_route(user_text)

        if route_result.get("route") != "change_request":
            st.warning("This input is not recognized as a change request.")
            st.json(route_result)
        else:
            conn = get_demo_connection()

            result = submit_add_datafile_request(
                conn=conn,
                user_text=user_text
            )

            st.session_state.last_change_result = result
            st.session_state.last_request_id = result.get("request_id", "")
            st.session_state.last_execution_result = None

            if result.get("success"):
                st.success(f"Request {result.get('request_id')} submitted successfully.")
            else:
                st.error("Request submission failed.")

    if st.session_state.last_change_result:
        render_recommendation(st.session_state.last_change_result)

        st.markdown("---")
        st.subheader("Latest Request Status")

        latest_request_id = st.session_state.last_request_id
        if latest_request_id:
            status_result = get_change_request_status(latest_request_id)
            if status_result.get("success"):
                st.json(status_result.get("record"))
            else:
                st.error(status_result.get("message"))

    if st.session_state.last_execution_result:
        st.markdown("---")
        render_execution_result(st.session_state.last_execution_result)

    st.markdown("---")
    render_pending_requests()


if __name__ == "__main__":
    main()