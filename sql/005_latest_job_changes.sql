
WITH latest_runs AS (
    SELECT
        run_id,
        ROW_NUMBER() OVER (
            ORDER BY finished_at DESC, run_id DESC
        ) AS run_rank
    FROM (
        SELECT run_id, finished_at
        FROM public.collection_runs
        WHERE source = 'booking'
          AND status = 'success'
        ORDER BY finished_at DESC, run_id DESC
        LIMIT 2
    ) AS recent_runs
),

previous_jobs AS (
    SELECT s.source_job_id
    FROM public.job_snapshots s
    JOIN latest_runs r ON s.run_id = r.run_id
    WHERE r.run_rank = 2
      AND s.source = 'booking'
),

current_jobs AS (
    SELECT s.source_job_id
    FROM public.job_snapshots s
    JOIN latest_runs r ON s.run_id = r.run_id
    WHERE r.run_rank = 1
      AND s.source = 'booking'
),

job_changes AS (
    SELECT
        COALESCE(p.source_job_id, c.source_job_id) AS job_id,
        CASE
            WHEN p.source_job_id IS NULL THEN 'new'
            WHEN c.source_job_id IS NULL THEN 'disappeared'
            ELSE 'existing'
        END AS job_status
    FROM previous_jobs p
    FULL OUTER JOIN current_jobs c
        ON p.source_job_id = c.source_job_id
)

SELECT
    job_status,
    COUNT(*) AS job_count
FROM job_changes
GROUP BY job_status
ORDER BY job_status;
