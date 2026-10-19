
import os
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv


SOURCES = ("booking", "uber")


def main():
    # Load database connection settings
    load_dotenv(Path(__file__).resolve().parent / ".env")

    database_url = os.environ["DATABASE_URL"]

    # Check only runs started during this workflow execution
    started_at = datetime.fromisoformat(
        os.environ["COLLECTION_STARTED_AT"].replace(
            "Z", "+00:00"
        )
    )

    errors = []

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            for source in SOURCES:
                cursor.execute(
                    """
                    SELECT
                        r.run_id,
                        r.status,
                        r.collected_job_count,
                        COUNT(s.source_job_id)
                    FROM public.collection_runs r
                    LEFT JOIN public.job_snapshots s
                        ON s.run_id = r.run_id
                        AND s.source = r.source
                    WHERE r.source = %s
                      AND r.finished_at >= %s
                    GROUP BY
                        r.run_id,
                        r.status,
                        r.collected_job_count
                    ORDER BY r.run_id DESC
                    LIMIT 1
                    """,
                    (source, started_at),
                )

                result = cursor.fetchone()

                if result is None:
                    errors.append(f"{source}: no completed run")
                    continue

                run_id, status, collected, snapshots = result

                print(
                    f"{source}: run={run_id}, "
                    f"status={status}, "
                    f"jobs={collected}, "
                    f"snapshots={snapshots}"
                )

                if status != "success":
                    errors.append(f"{source}: status={status}")
                elif not collected or collected != snapshots:
                    errors.append(
                        f"{source}: invalid job or snapshot count"
                    )

    if errors:
        raise RuntimeError("\n".join(errors))

    print("All collection checks passed!")


if __name__ == "__main__":
    main()
