import os
from dotenv import load_dotenv
import mysql.connector
import pandas as pd

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


def execute_query(query):
    conn = get_connection()
    try:
        df = pd.read_sql(query, conn)
    finally:
        conn.close()
    return df


def get_schema() -> str:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        lines = []
        for table in tables:
            cursor.execute(f"DESCRIBE `{table}`")
            cols = ", ".join(f"{c[0]} ({c[1]})" for c in cursor.fetchall())
            lines.append(f"{table}: {cols}")
        return "\n".join(lines)
    finally:
        conn.close()


def get_table_names():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        df = execute_query("SELECT * FROM customers LIMIT 5;")
        print("Sample records from customers table:")
        print(df)
    except Exception as e:
        print("Database connection or test query failed:", e)