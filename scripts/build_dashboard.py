
import os
from pathlib import Path

import altair as alt
import pandas as pd
import psycopg
from dotenv import load_dotenv



# Load database credentials from the local environment
project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

# Read the latest Amsterdam vacancies from PostgreSQL
with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT
                source_job_id::text AS job_id,
                title,
                posted_at::date AS posted_date
            FROM public.current_amsterdam_jobs
            WHERE posted_at IS NOT NULL
            ORDER BY posted_at, source_job_id
        """)

        records = cursor.fetchall()
        columns = [column.name for column in cursor.description]

jobs = pd.DataFrame(records, columns=columns)

if jobs.empty:
    raise RuntimeError("No Amsterdam vacancies found in PostgreSQL")

jobs["posted_date"] = pd.to_datetime(jobs["posted_date"])


# Assign preliminary categories based on job titles
def classify_role(title):
    text = (title or "").lower()

    if "analyst" in text or "analytics" in text:
        return "Analytics"
    if "scientist" in text or "machine learning" in text:
        return "Data Science / ML"
    if "engineer" in text or "developer" in text:
        return "Engineering"
    if "product" in text:
        return "Product"
    return "Other"


jobs["role"] = jobs["title"].apply(classify_role)

print(f"Loaded {len(jobs)} vacancies from Neon")
print(jobs["role"].value_counts())




# Build dropdown options from actual job categories
role_options = ["All"] + sorted(jobs["role"].unique().tolist())

role_filter = alt.param(
    name="selected_role",
    value="All",
    bind=alt.binding_select(
        options=role_options,
        name="Role category: ",
    ),
)



# Apply the shared filter to the underlying dataset
filtered_jobs = alt.Chart(jobs).transform_filter(
    "selected_role === 'All' || datum.role === selected_role"
)


# Chart 1: Number of vacancies by posting date
date_chart = (
    filtered_jobs
    .mark_bar()
    .encode(
        x=alt.X(
            "yearmonthdate(posted_date):T",
            title="Posting date",
        ),
        y=alt.Y(
            "count():Q",
            title="Number of vacancies",
        ),
        tooltip=[
            alt.Tooltip(
                "yearmonthdate(posted_date):T",
                title="Posting date",
            ),
            alt.Tooltip(
                "count():Q",
                title="Vacancies",
            ),
        ],
    )
    .properties(
        title="Vacancies by Posting Date",
        width=650,
        height=220,
    )
)


# Chart 2: Number of vacancies by role category
role_chart = (
    filtered_jobs
    .mark_bar()
    .encode(
        x=alt.X(
            "count():Q",
            title="Number of vacancies",
        ),
        y=alt.Y(
            "role:N",
            title="Role category",
            sort="-x",
        ),
        tooltip=[
            alt.Tooltip("role:N", title="Role"),
            alt.Tooltip("count():Q", title="Vacancies"),
        ],
    )
    .properties(
        title="Vacancies by Role",
        width=650,
        height=180,
    )
)


# Combine both charts and attach the shared filter
dashboard = (
    alt.vconcat(
        date_chart,
        role_chart,
        spacing=30,
    )
    .add_params(role_filter)
    .properties(
        title="Amsterdam Job Market Analytics — Demo"
    )
)


# Export the dashboard as a static HTML page
project_root = Path(__file__).resolve().parents[1]
site_dir = project_root / "site"
site_dir.mkdir(exist_ok=True)

output_file = site_dir / "index.html"

dashboard.save(
    output_file,
    embed_options={"actions": False},
)

print(f"Dashboard created: {output_file}")
