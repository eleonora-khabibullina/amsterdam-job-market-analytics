
import json
import time
from pathlib import Path

import requests


API_URL = "https://jobs.booking.com/api/jobs"
PAGE_SIZE = 10


def fetch_all_jobs():
    all_jobs = []
    page = 1
    expected_total_count = None

    while True:
        # Request the current page
        response = requests.get(
            API_URL,
            params={"page": page, "limit": PAGE_SIZE},
            timeout=20,
        )
        response.raise_for_status()

        data = response.json()
        jobs = data["jobs"]
        reported_count = data["totalCount"]

        # Check that the reported total remains consistent
        if expected_total_count is None:
            expected_total_count = reported_count

            if expected_total_count == 0:
                raise RuntimeError("API returned zero jobs")

        elif reported_count != expected_total_count:
            raise RuntimeError(
                "API total count changed during collection: "
                f"{expected_total_count} -> {reported_count}"
            )

        # Add the received jobs to the collection
        all_jobs.extend(jobs)

        print(
            f"Page {page}: {len(jobs)} jobs received. "
            f"Total collected: {len(all_jobs)}"
        )

        # Stop when the expected number of jobs is collected
        if len(all_jobs) >= expected_total_count:
            break

        # Reject an incomplete collection
        if not jobs:
            raise RuntimeError(
                "Collection stopped before all jobs were received"
            )

        page += 1

        # Pause between API requests
        time.sleep(1)

    # Verify the total number of collected jobs
    if len(all_jobs) != expected_total_count:
        raise RuntimeError(
            f"Expected {expected_total_count} jobs, "
            f"but collected {len(all_jobs)}"
        )

    # Check that job IDs are present and unique
    job_ids = [
        job_record["data"].get("req_id")
        for job_record in all_jobs
    ]

    if any(job_id is None or job_id == "" for job_id in job_ids):
        raise RuntimeError("Some jobs have missing IDs")

    if len(set(job_ids)) != len(job_ids):
        raise RuntimeError("Duplicate job IDs detected")

    return all_jobs, expected_total_count


def main():
    jobs, total_count = fetch_all_jobs()

    # Build the output path relative to the project root
    project_root = Path(__file__).resolve().parents[2]
    output_path = project_root / "data/raw/booking_jobs_all.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save the combined result
    result = {
        "jobs": jobs,
        "totalCount": total_count,
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)

    # Display collection statistics
    job_ids = [job["data"]["req_id"] for job in jobs]

    print("\nCollection completed!")
    print("Jobs collected:", len(jobs))
    print("Unique job IDs:", len(set(job_ids)))
    print("Total jobs reported by API:", total_count)


if __name__ == "__main__":
    main()
