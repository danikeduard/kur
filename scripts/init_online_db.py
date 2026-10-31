"""Initialize the canonical PostgreSQL schema from init_online_db.sql."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine


def main() -> None:
    load_dotenv()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required.")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    sql_path = Path(__file__).with_name("init_online_db.sql")
    sql = sql_path.read_text(encoding="utf-8")
    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.begin() as connection:
        connection.exec_driver_sql(sql)
    print("LinguaPath PostgreSQL schema is ready.")


if __name__ == "__main__":
    main()
