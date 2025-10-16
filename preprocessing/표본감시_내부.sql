WITH base AS (
  SELECT b.*, TO_CHAR(TEST_DATE, 'YYYY-MM') AS YEAR_MONTH
  FROM FOR_PREDICT b
),
vre_first AS (
  SELECT *
  FROM base b
  WHERE "EVAN(R)" = 1
    AND TEST_DATE = (
      SELECT MIN(TEST_DATE)
      FROM base
      WHERE "EVAN(R)" = 1
        AND PATIENT_NO = b.PATIENT_NO
        AND SPEC_TYPE = b.SPEC_TYPE
        AND TO_CHAR(TEST_DATE, 'YYYY-MM') = b.YEAR_MONTH
    )
),
mrpa_first AS (
  SELECT *
  FROM base b
  WHERE ("PIMP(R)" = 1 OR "PMEM(R)" = 1)
    AND TEST_DATE = (
      SELECT MIN(TEST_DATE)
      FROM base
      WHERE ("PIMP(R)" = 1 OR "PMEM(R)" = 1)
        AND PATIENT_NO = b.PATIENT_NO
        AND SPEC_TYPE = b.SPEC_TYPE
        AND TO_CHAR(TEST_DATE, 'YYYY-MM') = b.YEAR_MONTH
    )
),
mrab_first AS (
  SELECT *
  FROM base b
  WHERE ("AIMP(R)" = 1 OR "AMEM(R)" = 1)
    AND TEST_DATE = (
      SELECT MIN(TEST_DATE)
      FROM base
      WHERE ("AIMP(R)" = 1 OR "AMEM(R)" = 1)
        AND PATIENT_NO = b.PATIENT_NO
        AND SPEC_TYPE = b.SPEC_TYPE
        AND TO_CHAR(TEST_DATE, 'YYYY-MM') = b.YEAR_MONTH
    )
),
mrsa_first AS (
  SELECT *
  FROM base b
  WHERE "OXA(R)" = 1
    AND TEST_DATE = (
      SELECT MIN(TEST_DATE)
      FROM base
      WHERE "OXA(R)" = 1
        AND PATIENT_NO = b.PATIENT_NO
        AND SPEC_TYPE = b.SPEC_TYPE
        AND TO_CHAR(TEST_DATE, 'YYYY-MM') = b.YEAR_MONTH
    )
),
vre_monthly AS (
  SELECT YEAR_MONTH, COUNT(*) AS VRE FROM vre_first GROUP BY YEAR_MONTH
),
mrpa_monthly AS (
  SELECT YEAR_MONTH, COUNT(*) AS MRPA FROM mrpa_first GROUP BY YEAR_MONTH
),
mrab_monthly AS (
  SELECT YEAR_MONTH, COUNT(*) AS MRAB FROM mrab_first GROUP BY YEAR_MONTH
),
mrsa_monthly AS (
  SELECT YEAR_MONTH, COUNT(*) AS MRSA FROM mrsa_first GROUP BY YEAR_MONTH
)

SELECT
  COALESCE(v.YEAR_MONTH, p.YEAR_MONTH, a.YEAR_MONTH, s.YEAR_MONTH) AS YEAR_MONTH,
  NVL(v.VRE, 0) AS VRE,
  NVL(p.MRPA, 0) AS MRPA,
  NVL(a.MRAB, 0) AS MRAB,
  NVL(s.MRSA, 0) AS MRSA,
  NVL(v.VRE, 0) + NVL(p.MRPA, 0) + NVL(a.MRAB, 0) + NVL(s.MRSA, 0) AS TOTAL_MONITORED
FROM vre_monthly v
FULL OUTER JOIN mrpa_monthly p ON v.YEAR_MONTH = p.YEAR_MONTH
FULL OUTER JOIN mrab_monthly a ON COALESCE(v.YEAR_MONTH, p.YEAR_MONTH) = a.YEAR_MONTH
FULL OUTER JOIN mrsa_monthly s ON COALESCE(v.YEAR_MONTH, p.YEAR_MONTH, a.YEAR_MONTH) = s.YEAR_MONTH
ORDER BY YEAR_MONTH;
