WITH filtered_resistance AS (
  SELECT *
  FROM FOR_PREDICT
  WHERE "CIMP(R)" = 1 OR "CMEM(R)" = 1 OR "CETP(R)" = 1
),
with_year AS (
  SELECT w.*, EXTRACT(YEAR FROM test_date) AS year
  FROM filtered_resistance w
),
first_occurrence AS (
  SELECT
    patient_no,
    spec_type,
    year,
    MIN(test_date) AS first_test_date
  FROM with_year
  GROUP BY patient_no, spec_type, year
),
final_filtered AS (
  SELECT w.*
  FROM with_year w
  JOIN first_occurrence f
    ON w.patient_no = f.patient_no
   AND w.spec_type = f.spec_type
   AND w.year = f.year
   AND w.test_date = f.first_test_date
),
with_month AS (
  SELECT w.*, (TO_CHAR(test_date, 'YYYY-MM')) AS year_month
  FROM final_filtered w
)
SELECT
  year_month,
  COUNT(*) AS CRE_내부
FROM with_month
GROUP BY year_month
ORDER BY year_month;
