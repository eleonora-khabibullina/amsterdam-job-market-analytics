
import os
from pathlib import Path

import gspread
import psycopg
from dotenv import load_dotenv


def export_to_sheets():
    # Load environment variables
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")

    database_url = os.environ["DATABASE_URL"]
    spreadsheet_id = os.environ["GOOGLE_SHEET_ID"]

    credentials_path = Path(
        os.environ["GOOGLE_SERVICE_ACCOUNT_FILE"]
    ).expanduser()

    # Retrieve current Amsterdam jobs from PostgreSQL
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    source_job_id AS job_id,
                    title,
                    city,
                    posted_at::date AS posted_date,
                    apply_url
                FROM public.current_amsterdam_jobs
                ORDER BY title
            """)

            jobs = cursor.fetchall()

    # Prevent accidentally clearing the sheet
    if not jobs:
        raise RuntimeError("No jobs found for export")

    # Prepare data for Google Sheets
    headers = [
        "job_id",
        "title",
        "city",
        "posted_date",
        "apply_url",
    ]

    rows = [
        [
            str(job_id),
            title or "",
            city or "",
            posted_date.isoformat() if posted_date else "",
            apply_url or "",
        ]
        for job_id, title, city, posted_date, apply_url in jobs
    ]

    values = [headers] + rows

    # Authenticate using the service account
    client = gspread.service_account(
        filename=str(credentials_path)
    )

    # Open the existing Google spreadsheet
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.sheet1

    print("Connected to Google Sheets:", spreadsheet.title)

    # Replace the previous snapshot with current jobs
    worksheet.clear()
    worksheet.update(
        range_name="A1",
        values=values,
        value_input_option="USER_ENTERED",
    )

    print("Export completed successfully!")
    print("Jobs exported:", len(rows))


if __name__ == "__main__":
    export_to_sheets()
