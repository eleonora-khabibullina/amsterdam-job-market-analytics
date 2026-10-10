
WITH previous_run AS (
    SELECT source_job_id
    FROM public.job_snapshots
    WHERE run_id = 1
      AND source = 'booking'
),

current_run AS (
    SELECT source_job_id
    FROM public.job_snapshots
    WHERE run_id = 2
      AND source = 'booking'
),

job_changes AS (
    SELECT
        COALESCE(p.source_job_id, c.source_job_id) AS job_id,

        CASE
            WHEN p.source_job_id IS NULL THEN 'new'
            WHEN c.source_job_id IS NULL THEN 'disappeared'
            ELSE 'existing'
        END AS job_status

    FROM previous_run p
    FULL OUTER JOIN current_run c
        ON p.source_job_id = c.source_job_id
)

SELECT
    job_status,
    COUNT(*) AS job_count
FROM job_changes
GROUP BY job_status
ORDER BY job_status;
