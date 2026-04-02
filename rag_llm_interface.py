#!/usr/bin/env python3
"""
Streamlit RAG LLM Interface
Run using:
streamlit run rag_llm_interface.py
"""

import streamlit as st
import requests
import pandas as pd

# CONFIG
API_URL = "http://127.0.0.1:8000/query/ask"

st.set_page_config(
    page_title="NL → SQL Debugger",
    layout="wide"
)

st.title("NL → SQL AI Interface")

# INPUT SECTION
schema = st.selectbox(
    "Select Database Schema",
    ["askdb", "sales_db", "ecommerce_db", "employee_db", "banking_db", "hospital_db"]
)

prompt = st.text_input("Enter your natural language query")

run_query = st.button("Run Query")

# RUN QUERY
if run_query:

    if not prompt or not prompt.strip():
        st.warning("Please enter a valid query.")
        st.stop()

    payload = {
        "prompt": prompt,
        "user_id": 1,
        "schema_name": schema
    }

    try:
        with st.spinner("Processing your query..."):
            response = requests.post(API_URL, json=payload, timeout=120)

    except requests.exceptions.RequestException as e:
        st.error(" Failed to connect to API")
        st.text(str(e))
        st.stop()

    status_code = response.status_code

    # STATUS DISPLAY 
    st.subheader("API Status")

    if status_code == 200:
        st.success(f" Success (200)")
    elif status_code == 400:
        st.warning(f" Bad Request (400)")
    elif status_code == 404:
        st.warning(f" Not Found (404)")
    elif status_code == 422:
        st.warning(f" Query Execution Failed (422)")
    elif status_code == 500:
        st.error(f" Server Error (500)")
    else:
        st.info(f"ℹ Status Code: {status_code}")

    # HANDLE NON-200 RESPONSE
    if status_code != 200:
        try:
            error_data = response.json()
            st.error(error_data.get("detail", "Unknown error"))
        except:
            st.error(response.text)
        st.stop()

    # VALID JSON
    try:
        data = response.json()
    except Exception:
        st.error("Invalid JSON returned from API")
        st.text(response.text)
        st.stop()

    # SHOW BACKEND STATUS (if present)
    backend_status = data.get("status", "unknown")
    st.markdown(f"**Backend Status:** `{backend_status}`")

    col1, col2 = st.columns(2)

    # LEFT: LLM OUTPUT
    with col1:

        st.subheader("LLM Generation")

        st.markdown("### Model Used")
        st.write(data.get("model_used", "vllm"))

        # SQL OUTPUT
        st.markdown("### Generated SQL")
        sql_query = data.get("sql_query")

        if sql_query and str(sql_query).strip():
            st.code(sql_query, language="sql")
        else:
            st.warning("No SQL generated")

        # EVALUATION
        st.markdown("### Evaluation Metrics")
        evaluation = data.get("evaluation", {})

        if evaluation:
            st.json(evaluation)
        else:
            st.info("No evaluation data available")

        # Confidence
        confidence = evaluation.get("confidence_score", 1)
        hallucination = evaluation.get("hallucination", False)

        if confidence >= 0.8:
            st.success(f"Confidence Score: {confidence}")
        elif confidence >= 0.5:
            st.warning(f"Confidence Score: {confidence}")
        else:
            st.error(f"Confidence Score: {confidence}")

        if hallucination:
            st.error(" Hallucination detected in generated SQL")

    # RIGHT: RAG CONTEXT
    with col2:

        st.subheader("Schema Retrieval (RAG)")

        filtered_schema = data.get("filtered_schema")

        if filtered_schema:
            st.code(filtered_schema)
        else:
            st.info("No filtered schema")

    st.divider()

    # RESULT TABLE
    st.subheader("Query Result")

    result = data.get("data") or data.get("result")

    if result and isinstance(result, list) and len(result) > 0:

        try:
            df = pd.DataFrame(result)
            st.dataframe(df, use_container_width=True)

            # Check negative values
            numeric_cols = df.select_dtypes(include=["float", "int"]).columns

            for col in numeric_cols:
                if (df[col] < 0).any():
                    st.warning(f" Negative values detected in column: {col}")

        except Exception as e:
            st.error("Error displaying results")
            st.text(str(e))

    else:
        st.info("No rows returned")

# SIDEBAR
st.sidebar.title("About")

st.sidebar.info(
"""
NL → SQL AI System

Features:
• Natural language to SQL  
• RAG schema retrieval  
• SQL hallucination detection  
• Confidence scoring  
• Query result visualization  
• API status monitoring  
"""
)

st.sidebar.title("Usage")

st.sidebar.markdown(
"""
1. Select a schema  
2. Enter a natural language query  
3. Click Run Query  
4. View generated SQL and results  
"""
)