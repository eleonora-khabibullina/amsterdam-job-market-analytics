
import os
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from amsterdam_jobs.booking import fetch_all_jobs


SOURCE = "booking"


def create_run(database_url):
    # Register a new collection run
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.collection_runs (source, status)
                VALUES (%s, 'running')
                RETURNING run_id
                """,
                (SOURCE,),
            )

            return cursor.fetchone()[0]


def save_jobs(database_url, run_id, jobs, total_count):
    # Save all jobs and snapshots in one transaction
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            for job_record in jobs:
                job = job_record["data"]
                job_id = str(job["req_id"])

                posted_date = job.get("posted_date")
                posted_at = (
                    datetime.fromisoformat(posted_date)
                    if posted_date
                    else None
                )

                # Insert new jobs or update existing ones
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
                        SOURCE,
                        job_id,
                        job["title"],
                        job.get("city"),
                        job.get("description"),
                        posted_at,
                        job.get("apply_url"),
                    ),
                )

                # Record the job's presence in this collection run
                cursor.execute(
                    """
                    INSERT INTO public.job_snapshots (
                        run_id,
                        source,
                        source_job_id
                    )
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (run_id, SOURCE, job_id),
                )

            # Mark the collection as successfully completed
            cursor.execute(
                """
                UPDATE public.collection_runs
                SET
                    status = 'success',
                    finished_at = NOW(),
                    reported_job_count = %s,
                    collected_job_count = %s
                WHERE run_id = %s
                """,
                (total_count, len(jobs), run_id),
            )


def mark_run_failed(database_url, run_id, error):
    # Record a failed collection run
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.collection_runs
                SET
                    status = 'failed',
                    finished_at = NOW(),
                    error_message = %s
                WHERE run_id = %s
                """,
                (str(error)[:1000], run_id),
            )


def main():
    # Load database credentials from the project root
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")

    database_url = os.environ["DATABASE_URL"]

    # Register the collection before requesting the API
    run_id = create_run(database_url)
    print("Collection run started:", run_id)

    try:
        # Request fresh data from Booking.com
        jobs, total_count = fetch_all_jobs()

        # Save jobs, snapshots, and the successful run status
        save_jobs(database_url, run_id, jobs, total_count)

    except Exception as error:
        mark_run_failed(database_url, run_id, error)
        raise

    print("\nPipeline completed successfully!")
    print("Run ID:", run_id)
    print("Jobs collected:", len(jobs))
    print("Snapshots created:", len(jobs))


if __name__ == "__main__":
    main()
