# 💬 QueryBae: GenAI Text-to-SQL Assistant

Ask business questions in plain English and get back SQL, results, and charts. QueryBae uses an LLM plus schema retrieval (RAG) to turn natural language into MySQL queries, runs them, and shows the answer in a Streamlit chat interface.

## ✨ Features

- **Natural language to SQL**: type a question, get a MySQL query.
- **RAG over the database schema**: only the most relevant tables are sent to the model, so it scales to large databases.
- **Auto-generated table descriptions**: built from columns, foreign keys, and sample rows.
- **Per-database knowledge files**: optional business rules in `knowledge/<db_name>.md`.
- **Visible assumptions**: the model states how it interpreted ambiguous terms.
- **Self-correcting**: failed queries are retried with the error message.
- **Safe by default**: only `SELECT` queries are executed.
- **Streamlit UI**: chat interface, SQL viewer, results table, auto bar chart, CSV download.

## 🏗️ How it works

```
Question → ChromaDB finds relevant tables → Prompt (schema + rules) → LLM (Groq) → SQL → MySQL → Results
```

1. `build_index.py` describes every table and stores the descriptions in ChromaDB (run once).
2. At question time, the most relevant tables are retrieved.
3. The LLM receives the question, retrieved schema, and rules, and returns SQL.
4. The SQL is checked, executed on MySQL, and shown in the UI.

## 🛠️ Tech stack

Python · Streamlit · MySQL · ChromaDB · Groq API (`openai/gpt-oss-120b`) · pandas · SQLAlchemy

## 📁 Project structure

```
QueryBae/
├── app.py              # Streamlit frontend
├── text_to_sql.py      # question -> SQL, retries, safety check
├── build_index.py      # builds the ChromaDB schema index
├── db.py               # MySQL connection and helpers
├── import_data.py      # loads CSVs into MySQL
├── knowledge/          # optional per-database business rules
├── Database/           # CSV data files
├── requirements.txt
└── .env.example
```

## 🚀 Getting started

**Prerequisites:** Python 3.10+, MySQL running locally, and a free API key from [console.groq.com](https://console.groq.com).

```bash
# 1. Clone and enter the project
git clone https://github.com/<your-username>/QueryBae.git
cd QueryBae

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
copy .env.example .env         # then fill in your values
```

Create the database in MySQL:

```sql
CREATE DATABASE querybae;
```

Load the data, build the schema index, and start the app:

```bash
python import_data.py
python build_index.py
streamlit run app.py
```

The app opens at http://localhost:8501.

## 💡 Example questions

- What is the total shipping cost of orders for each country?
- Top 5 customers by number of orders
- How many products does each supplier provide?

## 🔒 Security notes

- Never commit `.env`; it is git-ignored.
- Generated queries are limited to `SELECT`. For real use, connect with a **read-only MySQL user**.

## 🗺️ Roadmap

- Save verified question → SQL examples and retrieve them as few-shot context
- Support more databases (PostgreSQL, SQLite)
- Thumbs up / down feedback in the UI
- Docker setup

## 📄 License

MIT
