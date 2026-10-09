
import json
from pathlib import Path

# Define the path to the raw JSON file
file_path = Path("data/raw/booking_jobs.json")

# Load JSON data from the file
with file_path.open(encoding="utf-8") as file:
    data = json.load(file)

# Explore the top-level JSON structure
print("Top-level keys:", list(data.keys()))

jobs = data["jobs"]

print("Jobs data type:", type(jobs))
print("Jobs in response:", len(jobs))
print("Total jobs:", data["totalCount"])


# Inspect the first job posting
if jobs:
    first_job = jobs[0]

    # Access the nested job data
    job_data = first_job["data"]

    print("Job data type:", type(job_data))

    if isinstance(job_data, dict):
        print("Job data fields:", list(job_data.keys()))
    else:
        print("Job data sample:", str(job_data)[:300])
else:
    print("No jobs in the response")

