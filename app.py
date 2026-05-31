import streamlit as st
import pandas as pd
from tool_router import route_query
from ai_agent import explain_result
from tools.db_tools import get_db_summary

st.title("Oracle AI DBA Assistant")

@st.cache_data(ttl=10)
def cached_summary():
    return get_db_summary()

@st.cache_data(ttl=10)
def cached_route_query(q):
    return route_query(q)

# UI
question = st.text_input("Ask a database question")

if question:
    st.subheader("Processing your request…")

    # Route to DBA task or backup generator
    data = cached_route_query(question)

    # If backup command (logical or physical)
    if isinstance(data, dict) and data.get("type") in ("logical_backup", "physical_backup"):
        st.subheader("Generated Backup Command")
        st.code(data["command"], language="bash")
        st.write(data["explanation"])
    else:
        # Normal SQL result
        st.subheader("Database Result")
        if isinstance(data, pd.DataFrame):
            st.dataframe(data)
        else:
            st.write(data)

        # AI explanation
        explanation = explain_result(question, data)
        st.subheader("AI Explanation")
        st.write(explanation)
