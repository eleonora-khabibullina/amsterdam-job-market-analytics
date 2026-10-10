
import json
import time
from pathlib import Path

import requests


API_URL = "https://jobs.booking.com/api/jobs"
PAGE_SIZE = 10


def fetch_all_jobs():
    all_jobs = []
    page = 1

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
        total_count = data["totalCount"]

        # Add the received jobs to the collection
        all_jobs.extend(jobs)

        print(
            f"Page {page}: {len(jobs)} jobs received. "
            f"Total collected: {len(all_jobs)}"
        )

        # Stop when all jobs have been collected
        if len(all_jobs) >= total_count or not jobs:
            break

        page += 1

        # Pause between API requests
        time.sleep(1)

    return all_jobs, total_count


def main():
    jobs, total_count = fetch_all_jobs()

    # Save the combined result
    output_path = Path("data/raw/booking_jobs_all.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "jobs": jobs,
        "totalCount": total_count,
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)

    # Check for duplicate job IDs
    job_ids = [job["data"].get("req_id") for job in jobs]

    print("\nCollection completed!")
    print("Jobs collected:", len(jobs))
    print("Unique job IDs:", len(set(job_ids)))
    print("Total jobs reported by API:", total_count)


if __name__ == "__main__":
    main()
