import os
import streamlit as st
import pandas as pd
import requests

# ===== NEW BLOCK START: Added imports for add datafile activity =====
from workflow_router import detect_change_request_route
from tools.change_tool import (
    submit_add_datafile_request,
    get_change_request_status,
    list_pending_change_requests,
    approve_change_request,
    reject_change_request,
    execute_change_request
)
from workflows.change_executor import oracle_alter_tablespace_callback
# ===== NEW BLOCK END =====


# ── MCP helper ─────────────────────────────────────────────
MCP_URL = "http://127.0.0.1:8000/mcp/execute"


def call_mcp(tool: str, params: dict):
    try:
        res = requests.post(
            MCP_URL,
            json={"tool": tool, "params": params},
            timeout=120
        )
        res.raise_for_status()
        return res.json()
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "❌ Cannot connect to MCP Server on port 8000"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "⏱ Request timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Page config ─────────────────────────────────────────────
st.set_page_config(page_title="Oracle AI DBA Assistant", layout="wide")
st.title("🗄️ Oracle AI DBA Assistant")
st.caption("Powered by Ollama · llama3:instruct · MCP Server")

# ── Session state initialization ────────────────────────────
if "workflow" not in st.session_state:
    st.session_state["workflow"] = None

if "execution_result" not in st.session_state:
    st.session_state["execution_result"] = None

if "query_result" not in st.session_state:
    st.session_state["query_result"] = None

# ===== NEW BLOCK START: Added session state for change request flow =====
if "last_change_request_id" not in st.session_state:
    st.session_state["last_change_request_id"] = ""

if "last_change_execution_result" not in st.session_state:
    st.session_state["last_change_execution_result"] = None
# ===== NEW BLOCK END =====


# ── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ MCP Server")
    if st.button("🔁 Check Health"):
        r = call_mcp("health", {})
        if r.get("status") == "MCP server running":
            st.success("✅ Online")
        else:
            st.error(f"❌ Offline — {r.get('error', '')}")

    st.divider()
    st.caption(f"Endpoint: {MCP_URL}")

    st.subheader("🔧 Query Mode")
    query_mode = st.radio(
        "Route queries via:",
        ["MCP Server", "Direct (legacy)"],
        index=0
    )

# ===== NEW BLOCK START: Helper functions for add datafile UI =====
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
    Mock DB identity for current safe app flow.
    Later this can be replaced with actual Oracle session DB identity.
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

    st.subheader("🧭 Target Database Context")

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
        f"Please verify the target DB before approval/execution: "
        f"{db_info.get('db_name')} / {db_info.get('instance_name')} / {db_info.get('service_name')}"
    )


def render_change_request_result(result):
    planner_result = result.get("planner_result", {})
    recommendation = planner_result.get("recommendation", {})
    policy_result = result.get("policy_result", {})
    approval_record = result.get("approval_record", {})
    request_id = result.get("request_id", "")

    st.subheader("🛠 Add Datafile Change Request")

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
    st.subheader("📦 Recommendation")
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
    st.subheader("✅ Validation Checks")
    render_check_table(recommendation.get("checks", []))

    st.markdown("---")
    st.subheader("🛡 Policy Result")
    st.write(f"**Allowed:** {policy_result.get('allowed')}")
    st.write(f"**Approval Required:** {policy_result.get('approval_required')}")
    st.write(f"**Execution Enabled:** {policy_result.get('execution_enabled')}")
    st.write(f"**Risk Level:** {policy_result.get('risk_level')}")
    st.write(f"**Environment:** {policy_result.get('environment_name')}")

    messages = policy_result.get("policy_messages", [])
    if messages:
        for msg in messages:
            st.write(f"- {msg}")

    st.markdown("---")
    st.subheader("✅ Approval / Execution Actions")

    if not request_id:
        st.warning("No request ID found.")
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

    col_a, col_b, col_c = st.columns(3)

    with col_a:
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

    with col_b:
        if st.button("Reject Request", key=f"reject_{request_id}"):
            rejection_result = reject_change_request(
                request_id=request_id,
                approver="Pravanjan",
                reason="Rejected from app review."
            )
            if rejection_result.get("success"):
                st.success(rejection_result.get("message"))
            else:
                st.error(rejection_result.get("message"))
            st.rerun()

    with col_c:
        execute_disabled = current_approval_status != "APPROVED"

        if st.button(
            "▶ Execute on Oracle",
            key=f"execute_{request_id}",
            disabled=execute_disabled
        ):
            # ── Real Oracle connection via existing get_connection() ────
            try:
                from db.db_connection import get_connection
                conn = get_connection()
            except Exception as conn_err:
                st.error(f"❌ Oracle connection failed: {conn_err}")
                st.stop()

            # ── Execute the approved change request ─────────────
            try:
                with st.spinner("Executing ALTER TABLESPACE on Oracle..."):
                    exec_result = execute_change_request(
                        request_id=request_id,
                        conn=conn,
                        dry_run=False,
                        executor_callback=oracle_alter_tablespace_callback
                    )
            finally:
                conn.close()

            st.session_state["last_change_execution_result"] = exec_result

            exec_status = exec_result.get("execution_status", "")
            if exec_status == "READY_FOR_MANUAL_EXECUTION":
                st.warning(exec_result.get("message"))
            elif exec_result.get("success"):
                st.success("✅ ALTER TABLESPACE executed successfully on Oracle.")
            else:
                st.error(exec_result.get("message"))

            st.rerun()

    if current_approval_status != "APPROVED":
        st.info("Execution button will be enabled only after approval.")

    st.info("This flow prepares the approved request for controlled execution handoff.")


def render_change_execution_result(execution_result):
    if not execution_result:
        return

    db_info = get_demo_db_identity()

    st.subheader("📊 Change Execution Result")
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
        st.code(
            f"-- Target DB: {db_info.get('db_name')} | "
            f"Instance: {db_info.get('instance_name')} | "
            f"Service: {db_info.get('service_name')}\n"
            f"{statement_preview}",
            language="sql"
        )

    verification_result = execution_result.get("verification_result", {})
    if verification_result:
        st.subheader("✔️ Verification Result")
        st.json(verification_result)


def render_pending_change_requests():
    st.subheader("🕒 Pending Change Requests")
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
# ===== NEW BLOCK END =====


# ==================================================
# DBA QUESTION SECTION
# ==================================================
st.header("💬 Database Assistant")

with st.form("db_question_form"):
    question = st.text_input(
        "Ask a database question",
        placeholder="e.g. show all tables in HR, show locked users, logical backup"
    )
    ask_btn = st.form_submit_button("🚀 Ask")

# ===== NEW BLOCK START: Replaced ask-button routing for add datafile =====
if ask_btn and question.strip():

    # -------------------------------------------------
    # CHANGE REQUEST ROUTE (Add Datafile)
    # -------------------------------------------------
    change_route = detect_change_request_route(question.strip())

    if change_route.get("route") == "change_request":
        try:
            from db.db_connection import get_connection
            conn = get_connection()

            with st.spinner("Processing add datafile change request..."):
                result = submit_add_datafile_request(
                    conn=conn,
                    user_text=question.strip()
                )

            result["route"] = "change_request"
            st.session_state["query_result"] = result
            st.session_state["last_change_request_id"] = result.get("request_id", "")
            st.session_state["last_change_execution_result"] = None

        except Exception as e:
            import traceback
            st.session_state["query_result"] = {
                "success": False,
                "route": "change_request",
                "error": f"{type(e).__name__}: {str(e)}\n\n{traceback.format_exc()}"
            }

    # -------------------------------------------------
    # MCP path
    # -------------------------------------------------
    elif query_mode == "MCP Server":
        with st.spinner("Querying Oracle via MCP..."):
            result = call_mcp("query", {"question": question.strip()})
            st.session_state["query_result"] = result

    # -------------------------------------------------
    # Direct/legacy path
    # -------------------------------------------------
    else:
        try:
            from tool_router import route_query
            from ai_agent import explain_result

            with st.spinner("Querying via direct tool router..."):
                data = route_query(question.strip())

            explanation = explain_result(question.strip(), data)

            st.session_state["query_result"] = {
                "success": True,
                "direct_mode": True,
                "data": data,
                "explanation": explanation
            }

        except Exception as e:
            st.session_state["query_result"] = {
                "success": False,
                "error": str(e)
            }
# ===== NEW BLOCK END =====


# ── Show stored query result ──────────────────────
if st.session_state["query_result"]:
    result = st.session_state["query_result"]

    if result.get("success"):

        # MCP Server Mode
        if not result.get("direct_mode"):
            if result.get("route"):
                st.caption(
                    f"Route: {result.get('route')} | "
                    f"Task: {result.get('task', 'N/A')} | "
                    f"Confidence: {result.get('confidence', 'N/A')}"
                )

            # ===== NEW BLOCK START: Change request result display =====
            if result.get("route") == "change_request":
                render_change_request_result(result)

                if st.session_state["last_change_execution_result"]:
                    st.markdown("---")
                    render_change_execution_result(
                        st.session_state["last_change_execution_result"]
                    )

                st.markdown("---")
                render_pending_change_requests()
            # ===== NEW BLOCK END =====

            # -------------------------------------------------
            # SOP Route Display (Phase 2 structured UI)
            # -------------------------------------------------
            elif result.get("route") == "sop":
                st.subheader("📘 SOP Guidance")

                if result.get("title"):
                    st.markdown(f"### {result.get('title')}")

                sop_sections = result.get("sop_sections", {})

                if sop_sections.get("purpose"):
                    st.markdown("#### 🎯 Purpose")
                    st.write(sop_sections["purpose"].strip())

                if sop_sections.get("steps"):
                    st.markdown("#### 🔢 Steps")
                    st.write(sop_sections["steps"].strip())

                if sop_sections.get("commands"):
                    st.markdown("#### 💻 Commands")
                    st.code(sop_sections["commands"].strip(), language="sql")

                if sop_sections.get("caution"):
                    st.markdown("#### ⚠️ Caution")
                    st.warning(sop_sections["caution"].strip())

                if sop_sections.get("validation"):
                    st.markdown("#### ✅ Validation")
                    st.write(sop_sections["validation"].strip())

                if sop_sections.get("other"):
                    st.markdown("#### 📄 Additional Details")
                    st.write(sop_sections["other"].strip())

                # Fallback if parsing did not work
                if not any(v.strip() for v in sop_sections.values() if isinstance(v, str)):
                    sop_content = result.get("sop_content") or result.get("explanation")
                    if sop_content:
                        st.markdown(sop_content)

                with st.expander("Technical details"):
                    if result.get("error"):
                        st.error(result.get("error"))
                    st.json({
                        "route": result.get("route"),
                        "task": result.get("task"),
                        "confidence": result.get("confidence")
                    })

            # -------------------------------------------------
            # Standard SQL / Known Task Display
            # -------------------------------------------------
            else:
                if result.get("sql"):
                    st.subheader("📝 Generated SQL")
                    st.code(result["sql"], language="sql")

                st.subheader("📊 Query Results")
                records = result.get("result", [])

                if records:
                    df = pd.DataFrame(records)
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"✅ {len(df)} row(s) returned")
                else:
                    st.info("Query executed — no rows returned.")

                if result.get("explanation"):
                    st.subheader("🤖 DBA Explanation")
                    st.write(result["explanation"])

        # Direct Legacy Mode
        else:
            st.subheader("📊 Database Result")
            data = result.get("data")

            if isinstance(data, pd.DataFrame):
                st.dataframe(data, use_container_width=True)
                st.caption(f"✅ {len(data)} row(s) returned")
            else:
                st.write(data)

            st.subheader("🤖 AI Explanation")
            st.write(result.get("explanation", "No explanation available."))

    else:
        if result.get("route"):
            st.caption(
                f"Route: {result.get('route')} | "
                f"Task: {result.get('task', 'N/A')} | "
                f"Confidence: {result.get('confidence', 'N/A')}"
            )

        if result.get("explanation"):
            st.subheader("🤖 DBA Explanation")
            st.write(result["explanation"])

        with st.expander("Technical details"):
            st.error(result.get("error", "Unknown error occurred"))

            if result.get("sql"):
                st.subheader("📝 Generated SQL")
                st.code(result["sql"], language="sql")

# ==================================================
# SCHEMA REFRESH SECTION
# ==================================================
st.divider()
st.header("🔄 Dynamic Schema Refresh")

col1, col2 = st.columns(2)
with col1:
    source_tns = st.text_input("Source TNS Alias", value="orclpdb")
    db_username = st.text_input("Database Username", value="system")

with col2:
    target_tns = st.text_input("Target TNS Alias", value="uatagent")
    db_password = st.text_input("Database Password", type="password")

schema_name = st.text_input("Schema Name", value="HR")

btn1, btn2, btn3 = st.columns(3)

with btn1:
    generate_plan = st.button("🔍 Analyze Refresh", use_container_width=True)

with btn2:
    execute_refresh = st.button("▶ Execute Refresh", use_container_width=True)

with btn3:
    clear_results = st.button("🗑 Clear Results", use_container_width=True)

if clear_results:
    st.session_state["workflow"] = None
    st.session_state["execution_result"] = None
    st.session_state["query_result"] = None
    # ===== NEW BLOCK START: Clear change request state =====
    st.session_state["last_change_request_id"] = ""
    st.session_state["last_change_execution_result"] = None
    # ===== NEW BLOCK END =====
    st.success("Results cleared")
    st.rerun()

# ── Analyze Refresh ───────────────────────────────
if generate_plan:
    with st.spinner("Generating refresh plan via MCP..."):
        result = call_mcp("refresh", {
            "source_tns": source_tns,
            "target_tns": target_tns,
            "username": db_username,
            "password": db_password,
            "schema_name": schema_name,
            "approved": False
        })

    if result.get("success"):
        st.session_state["workflow"] = result
        st.success("✅ Refresh Plan Generated")
    else:
        st.error(result.get("error", "Plan generation failed"))

# ── Execute Refresh ───────────────────────────────
if execute_refresh:
    with st.spinner("Executing schema refresh via MCP..."):
        result = call_mcp("refresh", {
            "source_tns": source_tns,
            "target_tns": target_tns,
            "username": db_username,
            "password": db_password,
            "schema_name": schema_name,
            "approved": True
        })

    st.session_state["execution_result"] = result

    if result.get("success"):
        st.success("✅ Workflow Completed Successfully")
    else:
        st.error(result.get("error", "❌ Workflow Failed"))

# ==================================================
# SHOW REFRESH PLAN
# ==================================================
if st.session_state["workflow"]:
    workflow = st.session_state["workflow"]

    st.subheader("📋 Refresh Plan")
    st.json(workflow)

    if workflow.get("report"):
        st.subheader("📄 DBA Report")
        st.text_area("Generated Report", workflow["report"], height=400)

# ==================================================
# SHOW EXECUTION RESULT
# ==================================================
if st.session_state["execution_result"]:
    result = st.session_state["execution_result"]

    st.subheader("📊 Execution Status")

    if result.get("success"):
        st.success("✅ Refresh completed successfully")
    else:
        st.error("❌ Refresh failed")

    if result.get("workflow"):
        st.subheader("🔁 Workflow Details")
        st.json(result["workflow"])

    if result.get("verification"):
        st.subheader("✔️ Verification Result")
        st.json(result["verification"])

    if result.get("errors") and len(result["errors"]) > 0:
        st.subheader("⚠️ Errors")
        st.json(result["errors"])