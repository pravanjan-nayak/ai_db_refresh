import streamlit as st
import pandas as pd
import requests

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

if ask_btn and question.strip():

    # ── MCP path ──────────────────────────────────
    if query_mode == "MCP Server":
        with st.spinner("Querying Oracle via MCP..."):
            result = call_mcp("query", {"question": question.strip()})
            st.session_state["query_result"] = result

    # ── Direct/legacy path ────────────────────────
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

            # -------------------------------------------------
            # SOP Route Display (Phase 2 structured UI)
            # -------------------------------------------------
            if result.get("route") == "sop":
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
