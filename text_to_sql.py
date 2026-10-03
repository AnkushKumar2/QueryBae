import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from db import execute_query

load_dotenv()
DB_NAME = os.getenv("DB_NAME")

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
MODEL_NAME = "openai/gpt-oss-120b"

chroma = chromadb.PersistentClient(path="chroma_db")
schema_collection = chroma.get_collection(f"schema_{DB_NAME}")

GENERIC_RULES = """- Write MySQL syntax.
- Use only tables and columns from the schema provided.
- Only write SELECT queries.
- Use table aliases and qualify column names in joins.
- If a term could match several columns, choose the most likely one and state it as the
  first line of your output in the form: -- Assumption: <what you chose and why>"""


def load_business_rules() -> str:
    path = os.path.join("knowledge", f"{DB_NAME}.md")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return ""


def get_relevant_schema(question: str, top_k: int = 5) -> str:
    results = schema_collection.query(query_texts=[question], n_results=top_k)
    return "\n\n".join(results["documents"][0])


def clean_sql(sql: str) -> str:
    lines = sql.strip().splitlines()
    return "\n".join(l for l in lines if not l.strip().startswith("```")).strip()


def is_safe(sql: str) -> bool:
    lines = [l for l in sql.splitlines() if not l.strip().startswith("--")]
    body = " ".join(lines).strip().lower()
    return body.startswith(("select", "with"))


def question_to_sql(question: str, feedback: str = "") -> str:
    system_prompt = (
        "You convert natural language business questions into SQL queries.\n\n"
        f"Rules:\n{GENERIC_RULES}\n\n"
        f"Rules specific to this database:\n{load_business_rules()}\n\n"
        f"Relevant schema:\n{get_relevant_schema(question)}\n\n"
        "Return only the SQL (plus the assumption comment). No other explanation."
    )
    user_msg = question + (f"\n\n{feedback}" if feedback else "")

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        temperature=0,
        max_tokens=1500,
    )
    return clean_sql(response.choices[0].message.content.strip())

def split_assumption(sql: str):
    lines = sql.splitlines()
    assumption, rest = None, []
    for line in lines:
        if line.strip().lower().startswith("-- assumption:"):
            assumption = line.split(":", 1)[1].strip()
        else:
            rest.append(line)
    return assumption, "\n".join(rest).strip()


def answer(question: str):
    """Returns (sql, dataframe_or_None, error_or_None). Retries failed queries twice."""
    sql = question_to_sql(question)
    for _ in range(3):
        if not is_safe(sql):
            return sql, None, "Only SELECT queries are allowed."
        try:
            return sql, execute_query(sql), None
        except Exception as e:
            sql = question_to_sql(
                question, f"Your previous SQL failed:\n{sql}\nError: {e}\nFix it."
            )
    return sql, None, "Could not produce a working query."


if __name__ == "__main__":
    question = "What is the total shipping cost of orders for each country?"
    sql, df, error = answer(question)
    print("Generated SQL:\n", sql)
    print("\nError:" if error else "\nQuery Results:")
    print(error if error else df)