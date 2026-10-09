
import json
from pathlib import Path

import requests


def fetch_booking_jobs():
    url = "https://jobs.booking.com/api/jobs"

    params = {
        "page": 1,
        "limit": 10,
    }

    response = requests.get(
        url,
        params=params,
        timeout=20,
    )

    print("HTTP status:", response.status_code)
    response.raise_for_status()

    data = response.json()

    output_path = Path("data/raw/booking_jobs.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    print("Data saved to:", output_path)
    print("Response type:", type(data).__name__)

    if isinstance(data, dict):
        print("JSON fields:", list(data.keys()))


if __name__ == "__main__":
    fetch_booking_jobs()
