import os
import pandas as pd
from sqlalchemy import create_engine


# Folder containing the CSVs: QueryBae/Database
base = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base, "Database")

from sqlalchemy.engine import URL

engine = create_engine(
    URL.create(
        "mysql+pymysql",
        username="root",
        password=os.getenv("DB_PASSWORD"),
        host="localhost",
        port=3306,
        database="querybae",
    )
)

# order matters because of foreign keys
tables = ["customers", "suppliers", "products", "orders", "order_details"]

for t in tables:
    df = pd.read_csv(os.path.join(data_dir, f"{t}.csv"))
    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"]).dt.date
    df.to_sql(t, engine, if_exists="append", index=False)
    print(f"{t}: {len(df)} rows imported")