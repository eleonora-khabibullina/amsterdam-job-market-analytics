
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


def check_connection():
    # Load environment variables from the project root
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    # Connect to PostgreSQL
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:

            # Check the database connection and table
            cursor.execute("""
                SELECT
                    current_database(),
                    COUNT(*)
                FROM public.job_postings
            """)

            database_name, job_count = cursor.fetchone()

            print("Connected to:", database_name)
            print("Jobs in database:", job_count)


if __name__ == "__main__":
    check_connection()
