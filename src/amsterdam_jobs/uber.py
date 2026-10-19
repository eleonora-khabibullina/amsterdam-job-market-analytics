
import re

from bs4 import BeautifulSoup

import time

import requests


SOURCE = "uber"

API_URL = (
    "https://iaziqy.fa.ocs.oraclecloud.com"
    "/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
)


DETAILS_URL = API_URL.replace(
    "recruitingCEJobRequisitions",
    "recruitingCEJobRequisitionDetails",
)


def fetch_job_details(job_id):
    # Retrieve the complete job description
    params = {
        "onlyData": "true",
        "expand": "all",
        "finder": (
            f'ById;Id="{job_id}",siteNumber={SITE_NUMBER}'
        ),
    }

    response = requests.get(
        DETAILS_URL,
        params=params,
        headers={
            "Accept": "application/json",
            "User-Agent": "AmsterdamJobsResearch/1.0",
        },
        timeout=30,
    )

    response.raise_for_status()
    payload = response.json()

    items = payload.get("items", [])

    if len(items) != 1:
        raise RuntimeError(
            f"Expected one job for {job_id}, got {len(items)}"
        )

    detail = items[0]

    if str(detail.get("Id")) != str(job_id):
        raise RuntimeError(
            f"Job ID mismatch for {job_id}"
        )

    return detail


SITE_NUMBER = "CX_1"
PAGE_SIZE = 100


def fetch_page(offset=0):
    # Request a page of job requisitions
    params = {
        "onlyData": "true",
        "expand": "requisitionList",
        "finder": (
            f"findReqs;siteNumber={SITE_NUMBER},"
            f"limit={PAGE_SIZE},offset={offset}"
        ),
    }

    response = requests.get(
        API_URL,
        params=params,
        headers={
            "Accept": "application/json",
            "User-Agent": "AmsterdamJobsResearch/1.0",
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def extract_locations(job):
    # Collect primary and secondary job locations
    locations = []

    if job.get("PrimaryLocation"):
        locations.append(job["PrimaryLocation"])

    for field in ("secondaryLocations", "otherWorkLocations"):
        for location in job.get(field) or []:
            if isinstance(location, dict):
                name = (
                    location.get("Name")
                    or location.get("LocationName")
                )
                if name:
                    locations.append(name)

    return locations


def fetch_all_jobs():
    # Collect every page before filtering
    all_jobs = []
    offset = 0
    expected_total = None

    while True:
        payload = fetch_page(offset)

        if not payload.get("items"):
            raise ValueError("Uber API returned no search data")

        search = payload["items"][0]

        if search.get("Offset") != offset:
            raise RuntimeError(
                f"Unexpected offset: {search.get('Offset')}"
            )

        total = search.get("TotalJobsCount")
        if total is None:
            raise ValueError("Missing TotalJobsCount")

        if expected_total is None:
            expected_total = int(total)

        jobs = search.get("requisitionList")
        if not isinstance(jobs, list):
            raise ValueError("Missing requisitionList")

        if not jobs and len(all_jobs) < expected_total:
            raise RuntimeError("Pagination stopped unexpectedly")

        all_jobs.extend(jobs)

        print(
            f"Uber: {len(all_jobs)}/{expected_total} "
            "jobs collected"
        )

        if len(all_jobs) >= expected_total:
            break

        offset += len(jobs)
        time.sleep(1)

    # Validate completeness and unique identifiers
    job_ids = [str(job.get("Id")) for job in all_jobs]

    if len(all_jobs) != expected_total:
        raise RuntimeError("Incomplete collection")

    if any(job.get("Id") is None for job in all_jobs):
        raise RuntimeError("Job without an identifier")

    if len(job_ids) != len(set(job_ids)):
        raise RuntimeError("Duplicate job identifiers")

    
    
    # Enrich Amsterdam vacancies with full job details
    result = []

    for job in all_jobs:
        location = job.get("PrimaryLocation") or ""

        if "amsterdam" not in location.casefold():
            continue

        details = fetch_job_details(job["Id"])

        # Combine all available description fields
        description_html = "\n".join(
            value
            for value in [
                details.get("ExternalDescriptionStr"),
                details.get("ExternalResponsibilitiesStr"),
                details.get("ExternalQualificationsStr"),
            ]
            if isinstance(value, str) and value.strip()
        )

        description = html_to_text(description_html)

        if not description:
            raise RuntimeError(
                f"Missing description for job {job['Id']}"
            )

        normalized_job = {
            "req_id": str(job["Id"]),
            "title": details.get("Title") or job.get("Title"),
            "location": location,
            "posted_date": job.get("PostedDate"),
            "description": description,
            "category": details.get("Category"),
            "source": SOURCE,
            "raw_data": {
                "listing": job,
                "details": details,
            },
        }

        result.append({"data": normalized_job})

        print(
            f"Uber: enriched {len(result)} "
            f"- {normalized_job['title']}"
        )

        time.sleep(0.5)

    print(f"Uber: {len(result)} Amsterdam jobs enriched")

    return result, len(result)




def html_to_text(html_content):
    # Convert HTML into readable plain text
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    for tag in soup.find_all("br"):
        tag.replace_with("\n")

    for tag in soup.find_all(
        ["p", "li", "div", "h1", "h2", "h3"]
    ):
        tag.append("\n")

    text = soup.get_text(separator=" ")

    # Normalize whitespace while preserving paragraphs
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

