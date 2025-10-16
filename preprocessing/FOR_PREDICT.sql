CREATE TABLE FOR_PREDICT AS
WITH base_with_abbrs AS (
  SELECT
    patient_no, spec_type, org_name, abx_name, intp_code, test_date,
    CASE WHEN org_name LIKE '%Enterococcus faecium%' THEN 1 ELSE 0 END AS EFU,
    CASE WHEN org_name LIKE '%Enterococcus faecalis%' THEN 1 ELSE 0 END AS EFA,
    CASE WHEN org_name LIKE '%Pseudomonas aeruginosa%' THEN 1 ELSE 0 END AS PSA,
    CASE WHEN org_name LIKE '%Acinetobacter baumannii%' THEN 1 ELSE 0 END AS ABA,
    CASE WHEN org_name LIKE '%Staphylococcus aureus%' THEN 1 ELSE 0 END AS SAU,
    CASE
      WHEN org_name IN (
        'Escherichia coli', 'Escherichia hermanii', 'Escherichia vulneris',
        'Klebsiella aerogenes', 'Klebsiella ornithinolytica', 'Klebsiella oxytoca',
        'Klebsiella planticola', 'Klebsiella pneumoniae', 'Klebsiella variicola',
        'Enterobacter aerogenes', 'Enterobacter asburiae', 'Enterobacter bugandensis',
        'Enterobacter cloacae', 'Enterobacter gergoviae', 'Enterobacter kobei',
        'Enterobacter ludwigii', 'Enterobacter sakazakii',
        'Citrobacter amalonaticus', 'Citrobacter braakii', 'Citrobacter farmeri',
        'Citrobacter freundii', 'Citrobacter sedlakii', 'Citrobacter youngae',
        'Salmonella Group B', 'Salmonella Group C', 'Salmonella Group D', 'Salmonella species',
        'Proteus hauseri', 'Proteus mirabilis', 'Proteus penneri', 'Proteus vulgaris',
        'Morganella morganii', 'Providencia rettgeri', 'Providencia stuartii', 'Providencia vermicola',
        'Serratia grimesii', 'Serratia liquefaciens', 'Serratia marcescens',
        'Serratia nematodiphila', 'Serratia odorifera', 'Serratia plymuthica', 'Serratia rubidaea',
        'Hafnia alvei', 'Leclercia adecarboxylata'
      )
      THEN 1 ELSE 0
    END AS CRE
  FROM parsed_data_final
)

SELECT
  patient_no, spec_type, org_name, abx_name, intp_code, test_date,

  -- 균주명 약어 컬럼
  EFU, EFA, PSA, ABA, SAU, CRE,

  -- 항생제 내성 약어 컬럼들
  CASE
    WHEN (EFU = 1 OR EFA = 1)
         AND LOWER(abx_name) LIKE '%vancomycin%'
         AND intp_code = 'R'
    THEN 1 ELSE 0
  END AS "EVAN(R)",

  CASE
    WHEN PSA = 1 AND LOWER(abx_name) LIKE '%imipenem%' AND intp_code = 'R'
    THEN 1 ELSE 0
  END AS "PIMP(R)",

  CASE
    WHEN PSA = 1 AND LOWER(abx_name) LIKE '%meropenem%' AND intp_code = 'R'
    THEN 1 ELSE 0
  END AS "PMEM(R)",

  CASE
    WHEN ABA = 1 AND LOWER(abx_name) LIKE '%imipenem%' AND intp_code = 'R'
    THEN 1 ELSE 0
  END AS "AIMP(R)",

  CASE
    WHEN ABA = 1 AND LOWER(abx_name) LIKE '%meropenem%' AND intp_code = 'R'
    THEN 1 ELSE 0
  END AS "AMEM(R)",

  CASE
    WHEN SAU = 1 AND LOWER(abx_name) LIKE '%oxacillin%' AND intp_code = 'R'
    THEN 1 ELSE 0
  END AS "OXA(R)",

  CASE
    WHEN SAU = 1 AND LOWER(abx_name) LIKE '%vancomycin%' AND intp_code = 'R'
    THEN 1 ELSE 0
  END AS "SVAN(R)",

  CASE
    WHEN CRE = 1 AND LOWER(abx_name) LIKE '%imipenem%' AND intp_code = 'R'
    THEN 1 ELSE 0
  END AS "CIMP(R)",

  CASE
    WHEN CRE = 1 AND LOWER(abx_name) LIKE '%meropenem%' AND intp_code = 'R'
    THEN 1 ELSE 0
  END AS "CMEM(R)",

  CASE
    WHEN CRE = 1 AND LOWER(abx_name) LIKE '%ertapenem%' AND intp_code = 'R'
    THEN 1 ELSE 0
  END AS "CETP(R)"

FROM base_with_abbrs
WHERE intp_code = 'R';

