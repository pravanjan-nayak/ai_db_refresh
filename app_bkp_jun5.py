import streamlit as st
import pandas as pd

from tool_router import route_query
from ai_agent import explain_result

from workflows.schema_refresh import (
    create_schema_refresh_plan
)

from workflows.schema_refresh_workflow import (
    SchemaRefreshWorkflow
)

st.set_page_config(
    page_title="Oracle AI DBA Assistant",
    layout="wide"
)

st.title("Oracle AI DBA Assistant")

# ==================================================
# DBA QUESTION SECTION
# ==================================================

st.header("Database Assistant")

question = st.text_input(
    "Ask a database question"
)

if question:

    try:

        data = route_query(question)

        st.subheader(
            "Database Result"
        )

        if isinstance(
            data,
            pd.DataFrame
        ):

            st.dataframe(
                data,
                use_container_width=True
            )

        else:

            st.write(data)

        explanation = explain_result(
            question,
            data
        )

        st.subheader(
            "AI Explanation"
        )

        st.write(
            explanation
        )

    except Exception as e:

        st.error(
            f"Error: {str(e)}"
        )

# ==================================================
# SCHEMA REFRESH SECTION
# ==================================================

st.header(
    "Dynamic Schema Refresh"
)

col1, col2 = st.columns(2)

with col1:

    source_tns = st.text_input(
        "Source TNS Alias",
        value="orclpdb"
    )

    db_username = st.text_input(
        "Database Username",
        value="system"
    )

with col2:

    target_tns = st.text_input(
        "Target TNS Alias",
        value="uatagent"
    )

    db_password = st.text_input(
        "Database Password",
        type="password"
    )

schema_name = st.text_input(
    "Schema Name",
    value="HR"
)

button_col1, button_col2, button_col3 = st.columns(3)

with button_col1:

    generate_plan = st.button(
        "Analyze Refresh"
    )

with button_col2:

    execute_refresh = st.button(
        "Execute Refresh"
    )
with button_col3:
    clear_results = st.button(
        "Clear Results"
    )

if clear_results:

    st.session_state.pop(
        "workflow",
        None
    )

    st.session_state.pop(
        "execution_result",
        None
    )

    st.success(
        "Results cleared"
    )

    st.rerun()

# ==================================================
# ANALYZE REFRESH
# ==================================================

if generate_plan:

    try:

        workflow = (
            create_schema_refresh_plan(
                source_tns,
                target_tns,
                db_username,
                db_password,
                schema_name
            )
        )

        st.session_state[
            "workflow"
        ] = workflow

        st.success(
            "Refresh Plan Generated Successfully"
        )

    except Exception as e:

        st.error(
            f"Workflow Error: {str(e)}"
        )

# ==================================================
# EXECUTE REFRESH
# ==================================================

if execute_refresh:

    try:

        workflow_engine = (
            SchemaRefreshWorkflow()
        )

        result = (
            workflow_engine.execute(
                source_tns=source_tns,
                target_tns=target_tns,
                username=db_username,
                password=db_password,
                schema_name=schema_name,
                approved=True
            )
        )

        st.session_state[
            "execution_result"
        ] = result

        if result["success"]:

            st.success(
                "Workflow Completed Successfully"
            )

        else:

            st.error(
                "Workflow Failed"
            )

    except Exception as e:

        st.error(
            f"Execution Error: {str(e)}"
        )

# ==================================================
# SHOW REFRESH PLAN
# ==================================================

if "workflow" in st.session_state:

    workflow = (
        st.session_state[
            "workflow"
        ]
    )

    st.subheader(
        "Refresh Plan"
    )

    st.json(workflow)

    if workflow.get(
        "report"
    ):

        st.subheader(
            "DBA Report"
        )

        st.text_area(
            "Generated Report",
            workflow["report"],
            height=400
        )

# ==================================================
# SHOW EXECUTION RESULT
# ==================================================

if "execution_result" in st.session_state:

    result = (
        st.session_state[
            "execution_result"
        ]
    )

    st.subheader(
        "Execution Status"
    )

    st.write(
        f"Success: {result['success']}"
    )

    if result.get(
        "workflow"
    ):

        st.subheader(
            "Workflow Details"
        )

        st.json(
            result["workflow"]
        )

    if result.get(
        "verification"
    ):

        st.subheader(
            "Verification Result"
        )

        st.json(
            result["verification"]
        )

    if result.get(
        "errors"
    ) and len(
        result["errors"]
    ) > 0:

        st.subheader(
            "Errors"
        )

        st.json(
            result["errors"]
        )