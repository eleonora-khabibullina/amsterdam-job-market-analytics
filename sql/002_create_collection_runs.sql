
CREATE TABLE IF NOT EXISTS public.collection_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL
        CHECK (status IN ('running', 'success', 'failed')),
    reported_job_count INTEGER,
    collected_job_count INTEGER,
    error_message TEXT
);
