
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

from app.db.query_runner import PostgresClient
from app.db.validator import validate_sql, enforce_limit

from app.llm.generate_sql import generate_sql, fix_sql
from app.llm.explain_results import explain_results

from app.rag.context_service import get_retrieval_context
from app.rag.ingest import run_ingest

# -------------------------
# Session State (History)
# -------------------------
if "history" not in st.session_state:
    st.session_state.history = []


# -------------------------
# Page Config
# -------------------------
st.set_page_config(page_title="ATHL Analytics", layout="wide")

st.title("AthenaIQ")
st.caption("Ask questions about your data using AI")

# Keep embeddings aligned with the active schema docs.
run_ingest()


# -------------------------
# User Input
# -------------------------
user_input = st.text_input("Ask a question")


if user_input:

    with st.spinner("Running query..."):

        # Step 1 — Retrieve context
        retrieval_ctx = get_retrieval_context(user_input)
        context = retrieval_ctx.text

        # Step 2 — Generate SQL
        sql = generate_sql(user_input, context)

        st.subheader("Generated SQL")
        st.code(sql, language="sql")

        # Step 3 — Validate + Execute
        if validate_sql(sql):
            sql = enforce_limit(sql)

            client = PostgresClient()
            result = client.run_query(sql)

            # Retry on error
            if isinstance(result, dict) and "error" in result:
                st.warning("Retrying with fixed SQL...")

                fixed_sql = fix_sql(user_input, sql, result["error"], context)

                st.subheader("Fixed SQL")
                st.code(fixed_sql, language="sql")

                result = client.run_query(fixed_sql)
                sql = fixed_sql

        else:
            result = {"error": "Invalid SQL"}

    # -------------------------
    # Display Results
    # -------------------------
    if isinstance(result, list):
        st.subheader("Results")
        st.write(f"Rows returned: {len(result)}")
        st.dataframe(result, use_container_width=True)

        explanation = explain_results(user_input, sql, result)

        st.subheader("Explanation")
        st.write(explanation)
    else:
        st.error(result.get("error", "Unknown error"))

    # -------------------------
    # Debug: Retrieved Context
    # -------------------------
    with st.expander("Retrieved Context"):
        st.text(context)

    # -------------------------
    # Save to History
    # -------------------------
    st.session_state.history.append({
        "question": user_input,
        "sql": sql,
        "result": result
    })


# -------------------------
# Sidebar — Query History
# -------------------------
st.sidebar.title("Query History")

for item in reversed(st.session_state.history[-5:]):
    st.sidebar.write("**Q:**", item["question"])