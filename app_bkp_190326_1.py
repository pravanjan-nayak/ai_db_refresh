import streamlit as st
import pandas as pd
from tool_router import route_query
from ai_agent import explain_result

st.title("Oracle AI DBA Assistant")

question = st.text_input("Ask a database question")

if question:

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