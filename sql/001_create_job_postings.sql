
CREATE TABLE IF NOT EXISTS public.job_postings (
    source TEXT NOT NULL,
    source_job_id TEXT NOT NULL,
    title TEXT NOT NULL,
    city TEXT,
    description_html TEXT,
    posted_at TIMESTAMPTZ,
    apply_url TEXT,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (source, source_job_id)
);
