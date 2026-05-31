import os
import signal
import streamlit as st
import pandas as pd
from tool_router import route_query
from ai_agent import explain_result
from db_tools import get_db_summary

def stop_app():
    st.warning("Shutting down Oracle AI Assistant...")
    os.kill(os.getpid(), signal.SIGTERM)

st.title("Oracle AI DBA Assistant")

question = st.text_input("Ask a database question")

if question:

    if question.lower() in ["exit", "quit", "shutdown"]:
        stop_app()

    elif question.lower() in ["summary", "dashboard", "status", "health check"]:
        with st.spinner("Analyzing database..."):
            data = get_db_summary()
            
            explanation = explain_result(question, data)
            
            st.header("Database Summary")
            st.subheader("DB Status")
            st.dataframe(data["database_status"])
            st.subheader("Top Wait Events")
            st.dataframe(data["top_waits"])
            st.subheader("Active Sessions")
            st.dataframe(data["active_sessions"])
            st.subheader("Tablespace Usage")
            st.dataframe(data["tablespace"])
            st.subheader("Top SQLs by Elapsed Time")
            st.dataframe(data["top_sql"])
            
            st.subheader("AI Explanation")
            st.write(explanation)

    else:
        with st.spinner("Analyzing database..."):
        
            data = route_query(question)
        
            explanation = explain_result(question, data)
        
            st.subheader("Database Result")
        
            # Display dataframe nicely
            if isinstance(data, pd.DataFrame):
                st.dataframe(data)
        
                if "USED_PERCENT" in data.columns:
                    st.subheader("Tablespace Usage Chart")
                    st.bar_chart(data.set_index("TABLESPACE_NAME"))
        
            else:
                st.write(data)
        
            st.subheader("AI Explanation")
            st.write(explanation)