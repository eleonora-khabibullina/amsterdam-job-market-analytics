
CREATE TABLE IF NOT EXISTS public.job_snapshots (
    run_id BIGINT NOT NULL,
    source TEXT NOT NULL,
    source_job_id TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (run_id, source, source_job_id),

    FOREIGN KEY (run_id)
        REFERENCES public.collection_runs(run_id),

    FOREIGN KEY (source, source_job_id)
        REFERENCES public.job_postings(source, source_job_id)
);
