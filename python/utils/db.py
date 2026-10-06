import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def get_engine():
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME"),
    )

    return create_engine(url, pool_pre_ping=True)


if __name__ == "__main__":
    engine = get_engine()

    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT
                    current_user,
                    current_database(),
                    version();
                """
            )
        ).fetchone()

        print("Database connection successful")
        print(f"User: {result[0]}")
        print(f"Database: {result[1]}")
        print(f"PostgreSQL: {result[2]}")
