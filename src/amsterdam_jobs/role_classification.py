
import re


def classify_role(title: str) -> str:
    # Normalize the job title
    title = " ".join(title.casefold().split())

    # Identify core analytics positions
    if re.search(
        r"\b(?:data|product|bi|business intelligence)\s+analyst\b",
        title,
    ):
        return "core_analytics"

    # Identify data science and machine learning positions
    if re.search(
        r"\b(?:data scientist|machine learning|ml engineer|"
        r"quantitative researcher|quant researcher)\b",
        title,
    ):
        return "data_science_ml"


    # Identify analytics engineering positions
    if re.search(r"\banalytics engineer\b", title):
        return "adjacent_analytics"

    # Identify business and financial analysts
    analyst_pattern = r"\banalyst\b"

    business_domains = (
        r"\b(?:commercial|strategy|financial|finance|"
        r"business|marketing|pricing|growth|fp&a)\b"
    )

    if (
        re.search(analyst_pattern, title)
        and re.search(business_domains, title)
    ):
        return "adjacent_analytics"

    # Leave unmatched roles for manual review
    return "needs_review"
