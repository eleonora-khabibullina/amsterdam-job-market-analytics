
import os
import re
from collections import Counter
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from amsterdam_jobs.role_classification import classify_role


def main():
    # Load database configuration
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    # Retrieve current Amsterdam jobs
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT source_job_id, title
                FROM public.current_amsterdam_jobs
                ORDER BY title
            """)
            jobs = cursor.fetchall()

    # Classify each job title
    results = [
        (job_id, title, classify_role(title))
        for job_id, title in jobs
    ]

    # Display job classifications for review
    for job_id, title, category in results:
        print(f"{job_id} | {category} | {title}")

    # Summarize the classification results
    counts = Counter(category for _, _, category in results)

    print("\nClassification summary:")
    for category, count in sorted(counts.items()):
        print(f"{category}: {count}")

    print("Total jobs:", len(results))


    # Identify titles that may require additional review
    review_pattern = re.compile(
        r"\b(?:analyst|analytics|data|insights?|"
        r"strategy|strategic|pricing|growth|"
        r"research|intelligence|reporting|governance)\b",
        re.IGNORECASE,
    )

    print("\n--- Classified analytics and data science roles ---")

    for job_id, title, category in results:
        if category != "needs_review":
            print(f"{job_id} | {category} | {title}")

    print("\n--- Potentially relevant roles requiring review ---")

    for job_id, title, category in results:
        if category == "needs_review" and review_pattern.search(title):
            print(f"{job_id} | {title}")



if __name__ == "__main__":
    main()
