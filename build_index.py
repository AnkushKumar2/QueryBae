import os
import time
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
from db import get_connection

load_dotenv()



db = os.getenv("DB_NAME")  


llm = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
MODEL = "openai/gpt-oss-120b"

def describe_table(cur, table):
    cur.execute(f"DESCRIBE `{table}`")
    cols = ", ".join(f"{c[0]} ({c[1]})" for c in cur.fetchall())

    cur.execute("""
        SELECT column_name, referenced_table_name, referenced_column_name
        FROM information_schema.key_column_usage
        WHERE table_schema = DATABASE() AND table_name = %s
          AND referenced_table_name IS NOT NULL
    """, (table,))
    fks = "; ".join(f"{a} -> {b}.{c}" for a, b, c in cur.fetchall()) or "none"

    cur.execute(f"SELECT * FROM `{table}` LIMIT 3")
    samples = cur.fetchall()

    prompt = (
        f"Table: {table}\nColumns: {cols}\nForeign keys: {fks}\nSample rows: {samples}\n\n"
        "In 2 sentences, describe what one row represents and what the notable columns mean. "
        "Mention if any column is stored once per row of a parent entity (like freight per order)."
    )
    r = llm.chat.completions.create(model=MODEL, temperature=0, max_tokens=500,
                                    messages=[{"role": "user", "content": prompt}])
    desc = r.choices[0].message.content.strip()
    return f"Table: {table}\nDescription: {desc}\nColumns: {cols}\nForeign keys: {fks}"

chroma = chromadb.PersistentClient(path="chroma_db")
try:
    chroma.delete_collection(f"schema_{db}")
except Exception:
    pass
collection = chroma.create_collection(f"schema_{db}")

conn = get_connection()
cur = conn.cursor()
cur.execute("SHOW TABLES")
tables = [r[0] for r in cur.fetchall()]

for t in tables:
    collection.add(ids=[t], documents=[describe_table(cur, t)])
    print("indexed", t)
    time.sleep(1)
conn.close()
print(f"Done: {len(tables)} tables indexed into schema_{db}")