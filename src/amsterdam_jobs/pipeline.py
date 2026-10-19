
import os
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from amsterdam_jobs.booking import (
    fetch_all_jobs as fetch_booking_jobs,
)
from amsterdam_jobs.uber import (
    fetch_all_jobs as fetch_uber_jobs,
)


SOURCES = {
    "booking": fetch_booking_jobs,
    "uber": fetch_uber_jobs,
}


def create_run(database_url, source):
    # Register a collection run for the selected source
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.collection_runs (
                    source,
                    status
                )
                VALUES (%s, 'running')
                RETURNING run_id
                """,
                (source,),
            )

            return cursor.fetchone()[0]


def normalize_job(source, job):
    # Convert source-specific fields into a common format
    if source == "uber":
        details = (
            (job.get("raw_data") or {}).get("details") or {}
        )

        # Preserve original HTML in the database
        description_html = "\n\n".join(
            value
            for value in [
                details.get("ExternalDescriptionStr"),
                details.get("ExternalResponsibilitiesStr"),
                details.get("ExternalQualificationsStr"),
            ]
            if isinstance(value, str) and value.strip()
        )

        if not description_html:
            description_html = job.get("description")

        location = job.get("location") or ""
        city = location.split(",")[0].strip() or None

    else:
        # Preserve the existing Booking.com field mapping
        description_html = job.get("description")
        city = job.get("city")

    return {
        "source_job_id": str(job["req_id"]),
        "title": job["title"],
        "city": city,
        "description_html": description_html,
        "posted_date": job.get("posted_date"),
        "apply_url": job.get("apply_url"),
    }


def save_jobs(database_url, run_id, source, jobs, total_count):
    # Save jobs and snapshots in a single transaction
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            for job_record in jobs:
                job = normalize_job(
                    source,
                    job_record["data"],
                )

                posted_date = job["posted_date"]
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
                        source,
                        job["source_job_id"],
                        job["title"],
                        job["city"],
                        job["description_html"],
                        posted_at,
                        job["apply_url"],
                    ),
                )

                # Record job presence in this collection run
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
                    (
                        run_id,
                        source,
                        job["source_job_id"],
                    ),
                )

            # Mark the collection as successful
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
    # Record an unsuccessful collection
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
    failed_sources = []

    for source, fetcher in SOURCES.items():
        print(f"\nCollecting jobs from {source}...")

        run_id = create_run(database_url, source)
        print("Collection run started:", run_id)

        try:
            jobs, total_count = fetcher()

            save_jobs(
                database_url,
                run_id,
                source,
                jobs,
                total_count,
            )

            print(f"{source}: collection successful")
            print("Run ID:", run_id)
            print("Jobs collected:", len(jobs))

        except Exception as error:
            mark_run_failed(database_url, run_id, error)
            failed_sources.append(source)
            print(f"{source}: collection failed - {error}")

    if failed_sources:
        raise RuntimeError(
            "Failed sources: " + ", ".join(failed_sources)
        )

    print("\nAll sources collected successfully!")


if __name__ == "__main__":
    main()
