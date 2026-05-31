import streamlit as st
import pandas as pd
from tool_router import route_query
from ai_agent import explain_result
from db_tools import get_db_summary

st.title("Oracle AI DBA Assistant")

@st.cache_data(ttl=10)
def cached_summary():
    return get_db_summary()

@st.cache_data(ttl=10)
def cached_route_query(q):
    return route_query(q)

@st.cache_data(ttl=10)
def cached_explanation(q, data):
    return explain_result(q, data)

def safe_df(label, value):
    st.subheader(label)
    if isinstance(value, pd.DataFrame):
        st.dataframe(value)
    else:
        st.error(value)

question = st.text_input("Ask a database question")

if question:
    if question.lower() in ["exit", "quit", "shutdown"]:
        st.success("Session ended")
        st.stop()

    if question.lower() in ["summary", "dashboard", "status", "health check"]:
        with st.spinner("Analyzing database..."):
            data = cached_summary()
            explanation = cached_explanation(question, data)

        st.header("Database Summary")
        safe_df("DB Status", data["database_status"])
        safe_df("Top Wait Events", data["top_waits"])
        safe_df("Active Sessions", data["active_sessions"])
        safe_df("Tablespace Usage", data["tablespace"])
        safe_df("Top SQLs by Elapsed Time", data["top_sql"])

        st.subheader("AI Explanation")
        st.write(explanation)

    else:
        with st.spinner("Analyzing database..."):
            data = cached_route_query(question)
            explanation = cached_explanation(question, data)

        st.subheader("Database Result")

        if isinstance(data, pd.DataFrame):
            st.dataframe(data)

            if "USED_PERCENT" in data.columns:
                st.subheader("Tablespace Usage Chart")
                st.bar_chart(data.set_index("TABLESPACE_NAME"))

        else:
            st.write(data)

        st.subheader("AI Explanation")
        st.write(explanation)
