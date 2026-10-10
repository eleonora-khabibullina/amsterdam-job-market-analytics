
CREATE OR REPLACE VIEW public.current_amsterdam_jobs AS
WITH latest_run AS (
    SELECT run_id
    FROM public.collection_runs
    WHERE source = 'booking'
      AND status = 'success'
    ORDER BY finished_at DESC, run_id DESC
    LIMIT 1
)
SELECT
    j.source_job_id,
    j.title,
    j.city,
    j.description_html,
    j.posted_at,
    j.apply_url,
    s.run_id
FROM latest_run r
JOIN public.job_snapshots s
    ON s.run_id = r.run_id
    AND s.source = 'booking'
JOIN public.job_postings j
    ON j.source = s.source
    AND j.source_job_id = s.source_job_id
WHERE LOWER(TRIM(j.city)) = 'amsterdam';
