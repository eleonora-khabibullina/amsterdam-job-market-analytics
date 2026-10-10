
import json
import os
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv


def main():
    # Locate the project root directory
    project_root = Path(__file__).resolve().parents[2]

    # Load database credentials
    load_dotenv(project_root / ".env")
    database_url = os.environ["DATABASE_URL"]

    # Load raw Booking.com job postings
    file_path = project_root / "data/raw/booking_jobs_all.json"

    with file_path.open(encoding="utf-8") as file:
        data = json.load(file)

    jobs = data["jobs"]

    # Insert or update all job postings in a single transaction
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:

            for job_record in jobs:
                job = job_record["data"]

                # Convert the publication date
                posted_at = (
                    datetime.fromisoformat(job["posted_date"])
                    if job.get("posted_date")
                    else None
                )

                cursor.execute(
                    """
                    INSERT INTO public.job_postings (
                        source,
                        source_job_id,
                        title,
                        city,
                        description_html,
                        posted_at,
                        apply_url
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source, source_job_id)
                    DO UPDATE SET
                        title = EXCLUDED.title,
                        city = EXCLUDED.city,
                        description_html = EXCLUDED.description_html,
                        posted_at = EXCLUDED.posted_at,
                        apply_url = EXCLUDED.apply_url,
                        last_seen_at = NOW()
                    """,
                    (
                        "booking",
                        str(job["req_id"]),
                        job["title"],
                        job.get("city"),
                        job.get("description"),
                        posted_at,
                        job.get("apply_url"),
                    ),
                )

            # Check the number of saved Booking.com jobs
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM public.job_postings
                WHERE source = %s
                """,
                ("booking",),
            )

            saved_count = cursor.fetchone()[0]

    print("Jobs processed:", len(jobs))
    print("Booking.com jobs in database:", saved_count)


if __name__ == "__main__":
    main()
