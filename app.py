# ============================================================
# QueryBae - Text-to-SQL Assistant
# Run with: streamlit run app.py
# ============================================================

# -----------------------------
# Imports
# -----------------------------
import streamlit as st
import pandas as pd

from text_to_sql import answer, split_assumption
from db import get_table_names


# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="QueryBae | Text-to-SQL Assistant",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------
# Custom CSS
# -----------------------------
st.markdown(
    """
    <style>
        /* Main page */
        .main {
            padding-top: 1rem;
        }

        /* Gradient header */
        .querybae-header {
            padding: 2rem 2.25rem;
            border-radius: 18px;
            margin-bottom: 1.5rem;
            background:
                linear-gradient(
                    135deg,
                    #6d5dfc 0%,
                    #8b5cf6 45%,
                    #ec4899 100%
                );
            color: white;
            box-shadow: 0 10px 30px rgba(109, 93, 252, 0.18);
        }

        .querybae-header h1 {
            margin: 0;
            font-size: 2.4rem;
            font-weight: 800;
            letter-spacing: -0.03em;
        }

        .querybae-header p {
            margin: 0.5rem 0 0;
            font-size: 1.05rem;
            opacity: 0.92;
        }

        /* Cards */
        .querybae-card {
            padding: 1rem;
            border-radius: 14px;
            border: 1px solid rgba(128, 128, 128, 0.18);
            background: rgba(128, 128, 128, 0.04);
            margin-bottom: 1rem;
        }

        /* Sidebar spacing */
        section[data-testid="stSidebar"] {
            padding-top: 1rem;
        }

        /* Metrics */
        div[data-testid="stMetric"] {
            padding: 0.7rem;
            border-radius: 12px;
            border: 1px solid rgba(128, 128, 128, 0.15);
        }

        /* Chat spacing */
        div[data-testid="stChatMessage"] {
            margin-bottom: 0.5rem;
        }

        /* Example buttons */
        .example-label {
            font-size: 0.8rem;
            font-weight: 600;
            opacity: 0.65;
            margin-bottom: 0.5rem;
        }

        /* Hide unnecessary Streamlit decoration */
        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Session state initialization
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# -----------------------------
# Helper functions
# -----------------------------
def is_text_column(series: pd.Series) -> bool:
    """Return True when a Series is suitable as a categorical/text column."""
    return (
        pd.api.types.is_object_dtype(series)
        or pd.api.types.is_string_dtype(series)
        or pd.api.types.is_categorical_dtype(series)
    )


def is_numeric_column(series: pd.Series) -> bool:
    """Return True when a Series contains numeric values."""
    return pd.api.types.is_numeric_dtype(series)


def find_chart_columns(df: pd.DataFrame):
    """
    Find the first text column and first numeric column
    that can be used to create an automatic bar chart.
    """
    text_column = None
    numeric_column = None

    for column in df.columns:
        if text_column is None and is_text_column(df[column]):
            text_column = column

        if numeric_column is None and is_numeric_column(df[column]):
            numeric_column = column

        if text_column is not None and numeric_column is not None:
            break

    return text_column, numeric_column


def render_result(result: dict):
    """Render a stored assistant result."""
    assumption = result.get("assumption")
    sql = result.get("sql")
    df = result.get("df")
    error = result.get("error")

    # Model assumption
    if assumption:
        st.info(f"💡 **Model assumption:** {assumption}")

    # Generated SQL
    if sql:
        with st.expander("🔍 View generated SQL", expanded=False):
            st.code(sql, language="sql")

    # Error message
    if error:
        st.error(f"⚠️ {error}")
        return

    # No data returned
    if df is None:
        st.info("The query completed successfully, but returned no tabular result.")
        return

    # Results table
    st.markdown("#### 📊 Results")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    # Row count
    st.metric("Rows returned", len(df))

    # Automatic bar chart
    if not df.empty and len(df.columns) >= 2:
        text_column, numeric_column = find_chart_columns(df)

        if text_column and numeric_column:
            chart_df = df[[text_column, numeric_column]].copy()

            chart_df[text_column] = chart_df[text_column].astype(str)
            chart_df[numeric_column] = pd.to_numeric(
                chart_df[numeric_column],
                errors="coerce",
            )

            chart_df = chart_df.dropna(subset=[numeric_column])

            if not chart_df.empty:
                chart_df = chart_df.set_index(text_column)

                st.markdown("#### 📈 Quick visualization")
                st.bar_chart(chart_df[numeric_column])

    # CSV download
    csv_data = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download results as CSV",
        data=csv_data,
        file_name="querybae_results.csv",
        mime="text/csv",
        use_container_width=False,
    )


# -----------------------------
# Header
# -----------------------------
st.markdown(
    """
    <div class="querybae-header">
        <h1>💬 QueryBae</h1>
        <p>Ask questions in plain English. Query your database with SQL generated for you.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("## QueryBae")

    # Database connection status
    st.markdown("### 🔌 Database")

    try:
        table_names = get_table_names()

        st.success("Connected")

        if table_names:
            st.caption(f"{len(table_names)} table(s) available")
        else:
            st.warning("Connected, but no tables were found.")

    except Exception as exc:
        table_names = []
        st.error("Connection unavailable")
        st.caption(str(exc))

    # Tables
    if table_names:
        with st.expander("🗂️ Available tables", expanded=True):
            for table in table_names:
                st.markdown(f"• `{table}`")

    # Example questions
    st.markdown("### ✨ Try an example")
    st.markdown(
        '<div class="example-label">Click a question to run it</div>',
        unsafe_allow_html=True,
    )

    examples = [
        "Show me all customers.",
        "How many orders are there?",
        "Show the top 10 products by sales.",
        "What are the total sales by month?",
        "Which customers have placed the most orders?",
    ]

    for example in examples:
        if st.button(
            example,
            key=f"example_{example}",
            use_container_width=True,
        ):
            st.session_state.pending_question = example
            st.rerun()

    st.divider()

    # Clear chat
    if st.button(
        "🗑️ Clear chat",
        use_container_width=True,
        type="secondary",
    ):
        st.session_state.messages = []
        st.session_state.pending_question = None
        st.rerun()


# -----------------------------
# Display conversation history
# -----------------------------
for message in st.session_state.messages:
    role = message["role"]

    with st.chat_message(role):
        if role == "user":
            st.markdown(message["content"])

        elif role == "assistant":
            render_result(message["result"])


# -----------------------------
# Chat input
# -----------------------------
typed_question = st.chat_input(
    "Ask QueryBae something about your database..."
)

# Prioritize a clicked example question.
question = st.session_state.pending_question or typed_question

if question:
    # Reset pending example
    st.session_state.pending_question = None

    # Add user message to history
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    # Immediately display the user question
    with st.chat_message("user"):
        st.markdown(question)

    # Generate SQL and execute query
    with st.chat_message("assistant"):
        with st.spinner("QueryBae is thinking and querying your database..."):
            try:
                sql, df, error = answer(question)

                # Extract model assumption from generated SQL
                assumption, clean_sql = split_assumption(sql)

                result = {
                    "assumption": assumption,
                    "sql": clean_sql,
                    "df": df,
                    "error": error,
                }

            except Exception as exc:
                result = {
                    "assumption": None,
                    "sql": "",
                    "df": None,
                    "error": f"Something went wrong while processing your question: {exc}",
                }

        # Render result
        render_result(result)

    # Save assistant response
    st.session_state.messages.append(
        {
            "role": "assistant",
            "result": result,
        }
    )