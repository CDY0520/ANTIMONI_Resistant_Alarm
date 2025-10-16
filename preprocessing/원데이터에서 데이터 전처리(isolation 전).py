############### 원데이터에서 prophet 모델에 사용할 데이터로 전처리하기(최종) ##################
# 1. 라이브러리 임포트, 한글 폰트 설정
# 2. parse_multi_organism_and_resistance 함수 정의
# 3. 데이터 로드
# 4. 날짜 컬럼을 datetime 형식으로 변환
# 5. 특정 혈액 검체명들을 'Whole Blood'로 통일 (다른 검체명은 유지)
# 6. 검사결과에서 균주명 파싱(균주명 컬럼 생성) 및 한 행에 동정결과 2개인 경우 따로 행 확장
# 7. 균주명 약어 컬럼 생성
# 8. 항생제 내성 약어 컬럼 생성
# 9. 컬럼 리스트 및 추가된 컬럼 건수 확인
# 10. 최종 데이터 확정 및 저장
##########################################################################################



### --- 1. 라이브러리 임포트 및 한글 폰트 설정하기 ---

# 라이브러리 임포트
import pandas as pd
import re
import os
import matplotlib.pyplot as plt

# 한글 폰트 설정 (Windows 기준)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False  # 한글 폰트 사용 시 마이너스 부호 깨짐 방지





### --- 2. parse_multi_organism_and_resistance 함수 정의  ---
# 이 함수는 검사결과 텍스트에서 모든 동정결과와 해당 내성 패턴을 파싱합니다.
def parse_multi_organism_and_resistance(result_text):
    if not isinstance(result_text, str):
        return []
    results = []
    # 'No Growth' 패턴을 먼저 확인
    if "No Growth" in result_text:
        return [{'Organism': "No Growth", 'Resistance_Patterns': {}}]

    blocks = re.split(r'(?=동정결과:)', result_text, flags=re.MULTILINE)
    blocks = [block for block in blocks if block.strip().startswith('동정결과:')]

    for block in blocks:
        organism = None
        resistance_patterns = {}

        # 동정결과에서 균주명 파싱
        organism_match = re.search(r'동정결과:\s*([^,\n]+?)(?:,\s*정도:\s*.+?)?\s*(?:\n|$)', block, re.MULTILINE)
        if organism_match:
            organism = organism_match.group(1).strip()
            if organism.endswith('.'):
                organism = organism[:-1]

        # 항생제 감수성 결과 섹션 파싱
        resistance_section_match = re.search(
            r'항생제 감수성결과\s*\n-+\n(.+?)(?=\n\nCOMMENT:|\n\n\(최종보고\)|\Z)',
            block, re.DOTALL | re.IGNORECASE
        )

        if resistance_section_match:
            resistance_lines = resistance_section_match.group(1).strip().split('\n')
            for line in resistance_lines:
                # 각 항생제의 이름과 감수성 결과(S, I, R) 파싱
                match = re.search(r'(.+?)\s+([<>=]?[\d.]+)\s+\(([RS])\)', line.strip())
                if match:
                    antibiotic = match.group(1).strip()
                    judgment = match.group(3).strip()
                    resistance_patterns[antibiotic] = judgment

        if organism:
            results.append({'Organism': organism, 'Resistance_Patterns': resistance_patterns})
    return results





### --- 3. 데이터 로드 설정 ---
file_paths = [
    '미생물 배양 검사1.xlsx',
    '미생물 배양 검사2.xlsx',
    '미생물 배양 검사3.xlsx',
    '미생물 배양 검사4.xlsx',
    '미생물 배양 검사5.xlsx',
    '미생물 배양 검사6.xlsx',
    '미생물 배양 검사7.xlsx',
    '미생물 배양 검사8.xlsx',
    '미생물 배양 검사9.xlsx',
    '미생물 배양 검사10.xlsx',
    '미생물 배양 검사11.xlsx',
    '미생물 배양 검사12.xlsx',
    '미생물 배양 검사13.xlsx',
    '미생물 배양 검사14.xlsx'
]

all_dfs = []

print("--- 파일 로드 중 ---")
files_loaded_successfully = False
for f_path in file_paths:
    try:
        current_df = pd.read_excel(f_path)
        all_dfs.append(current_df)
        print(f"'{f_path}' 파일 성공적으로 로드.")
        files_loaded_successfully = True
    except FileNotFoundError:
        print(f"경고: '{f_path}' 파일을 찾을 수 없습니다. 이 파일은 건너뜜니다.")
    except Exception as e:
        print(f"오류: '{f_path}' 파일 로드 중 오류 발생: {e}")

if all_dfs:
    df_combined = pd.concat(all_dfs, ignore_index=True)
    print("\n--- 1. 모든 파일이 성공적으로 병합되었습니다. ---")
    print(f"모든 파일 병합 후 원본 데이터의 총 행 수: {len(df_combined)} 행")
    print("\n컬럼 목록:")
    print(df_combined.columns.tolist())
else:
    print("\n오류: 로드된 엑셀 파일이 없습니다. 프로그램을 종료합니다.")
    print("      지정된 경로에 엑셀 파일이 올바르게 존재하는지 확인해주세요.")
    exit()





### --- 4. 날짜 컬럼을 datetime 형식으로 변환 (검사시행일시만 사용) ---
if '검사시행일시' in df_combined.columns:
    df_combined['검사일자'] = pd.to_datetime(df_combined['검사시행일시'], errors='coerce')
else:
    print("오류: '검사시행일시' 컬럼이 없어 날짜 변환을 수행할 수 없습니다. 프로그램을 종료합니다.")
    exit()

df_combined.dropna(subset=['검사일자'], inplace=True)
print(f"\n--- 2. '검사일자' 컬럼 datetime 변환 완료 (검사시행일시만 사용). 총 {len(df_combined)}개 행 ---")






### --- 5. 특정 혈액 검체명들을 'Whole Blood'로 통일 (다른 검체명은 유지) ---
blood_specimen_types = [
    'Whole Blood(C line)',
    'Whole Blood(Cath)',
    'Whole Blood(Chemoport)',
    'Whole Blood(PICC1)',
    'Whole Blood(PICC2)',
    'Whole Blood(Peripheral)',
    'Whole Blood(성인)',
    'Whole Blood(소아)',
    'Serum(Blood)'
]

if '검체명(주검체)' in df_combined.columns:
    # isin()을 사용하여 blood_specimen_types에 해당하는 행만 선택하여 값을 변경
    df_combined.loc[df_combined['검체명(주검체)'].isin(blood_specimen_types), '검체명(주검체)'] = 'Whole Blood'
    print(f"\n--- 3. 지정된 혈액 검체명들을 'Whole Blood'로 통일 완료. 다른 검체명은 유지. ---")
else:
    print("오류: '검체명(주검체)' 컬럼이 데이터프레임에 없습니다. 검체명 통일을 건너뜁니다.")

# 이제 전체 데이터 (df_combined)를 가지고 다음 단계로 진행합니다. 혈액 검체만 필터링하는 단계는 없어집니다.
df_processed = df_combined.copy() # 이후 파싱 및 확장 작업을 위해 복사본 생성






### --- 6. 검사결과에서 균주명 파싱(균주명 컬럼 생성) 및 한 행에 동정결과 2개인 경우 따로 행 확장 ---
# '검사결과' 컬럼은 건드리지 않고, 파싱된 결과를 바탕으로 새 컬럼 생성
df_processed['Parsed_Results'] = df_processed['검사결과'].apply(parse_multi_organism_and_resistance)

# 'Parsed_Results'가 비어있지 않은 모든 행을 포함 (No Growth 포함)
# 균주명 추출 시 "No Growth" 또는 빈 리스트인 경우를 처리
df_expanded = df_processed.explode('Parsed_Results').copy()

# '균주명' 컬럼 추출
df_expanded['균주명'] = df_expanded['Parsed_Results'].apply(
    lambda x: x['Organism'] if isinstance(x, dict) and 'Organism' in x else None
)
# 'Parsed_Results' 임시 컬럼 제거
df_expanded = df_expanded.drop(columns=['Parsed_Results'])

# '균주명'이 "No Growth"인 경우 해당 값으로 유지, 그 외 파싱 실패한 경우 None
df_expanded['균주명'] = df_expanded['균주명'].apply(lambda x: x if x == "No Growth" else (x if x else None))

# 'No Growth' 결과 제거 (내성 모니터링 목적이므로)
df_expanded_filtered = df_expanded[df_expanded['균주명'] != "No Growth"].copy()
df_expanded_filtered.dropna(subset=['균주명'], inplace=True) # 균주명이 None인 행도 제거

print(f"\n--- 4. '검사결과'에서 균주명 파싱 및 행 확장 완료. 총 {len(df_expanded_filtered)}개 행 (No Growth 제외) ---")







# --- 7. 균주명 약어 컬럼 생성 ---
# '균주명' 컬럼에 해당 균 문자열이 포함되어 있으면 1, 아니면 0
# str(x)를 사용하여 NaN 값 등에 대한 오류 방지
# df_combined 대신 df_expanded_filtered 사용
df_expanded_filtered['EFU'] = df_expanded_filtered['균주명'].apply(lambda x: 1 if 'Enterococcus faecium' in str(x) else 0)
df_expanded_filtered['EFA'] = df_expanded_filtered['균주명'].apply(lambda x: 1 if 'Enterococcus faecalis' in str(x) else 0)
df_expanded_filtered['PSA'] = df_expanded_filtered['균주명'].apply(lambda x: 1 if 'Pseudomonas aeruginosa' in str(x) else 0)
df_expanded_filtered['ABA'] = df_expanded_filtered['균주명'].apply(lambda x: 1 if 'Acinetobacter baumannii' in str(x) else 0)
df_expanded_filtered['SAU'] = df_expanded_filtered['균주명'].apply(lambda x: 1 if 'Staphylococcus aureus' in str(x) else 0)

# CRE 컬럼 생성
cre_organisms = [
    'Escherichia coli',
    'Escherichia hermanii',
    'Escherichia vulneris',
    'Klebsiella aerogenes',
    'Klebsiella ornithinolytica',
    'Klebsiella oxytoca',
    'Klebsiella planticola',
    'Klebsiella pneumoniae',
    'Klebsiella variicola',
    'Enterobacter aerogenes',
    'Enterobacter asburiae',
    'Enterobacter bugandensis',
    'Enterobacter cloacae',
    'Enterobacter gergoviae',
    'Enterobacter kobei',
    'Enterobacter ludwigii',
    'Enterobacter sakazakii',
    'Citrobacter amalonaticus',
    'Citrobacter braakii',
    'Citrobacter farmeri',
    'Citrobacter freundii',
    'Citrobacter sedlakii',
    'Citrobacter youngae',
    'Salmonella Group B',
    'Salmonella Group C',
    'Salmonella Group D',
    'Salmonella species',
    'Proteus hauseri',
    'Proteus mirabilis',
    'Proteus penneri',
    'Proteus vulgaris',
    'Morganella morganii',
    'Providencia rettgeri',
    'Providencia stuartii',
    'Providencia vermicola',
    'Serratia grimesii',
    'Serratia liquefaciens',
    'Serratia marcescens',
    'Serratia nematodiphila',
    'Serratia odorifera',
    'Serratia plymuthica',
    'Serratia rubidaea',
    'Hafnia alvei',
    'Leclercia adecarboxylata',
]

# 'CRE' 컬럼 생성: cre_organisms 리스트 중 하나라도 '균주명'에 포함되면 1, 아니면 0
# df_combined 대신 df_expanded_filtered 사용
df_expanded_filtered['CRE'] = df_expanded_filtered['균주명'].apply(
    lambda x: 1 if any(organism in str(x) for organism in cre_organisms) else 0
)

print("\n --- 균주명 약어 컬럼 생성 완료 ---")
print("생성된 약어 컬럼 목록:", ['EFU', 'EFA', 'PSA', 'ABA', 'SAU', 'CRE'])










# --- 8. 항생제 내성 약어 컬럼 생성 ---

# 모든 새로운 항생제 내성 컬럼을 0으로 초기화
new_resistance_cols = ['EVAN(R)', 'PIMP(R)', 'PMEM(R)', 'AIMP(R)', 'AMEM(R)', 'OXA(R)', 'SVAN(R)', 'CIMP(R)', 'CMEM(R)', 'CETP(R)']
# df_combined 대신 df_expanded_filtered 사용
for col in new_resistance_cols:
    df_expanded_filtered[col] = 0

# EFU, EFA 둘 중 하나라도 1이면서 Vancomycin(R)인 경우 EVAN(R)
# str.contains를 사용하여 대소문자 구분 없이 'Vancomycin'을 찾고, 정확히 '(R)'을 포함하는지 확인
# regex=False로 하여 (R)을 리터럴 문자열로 인식
# df_combined 대신 df_expanded_filtered 사용
df_expanded_filtered.loc[
    ((df_expanded_filtered['EFU'] == 1) | (df_expanded_filtered['EFA'] == 1)) &
    df_expanded_filtered['검사결과'].str.contains('Vancomycin', case=False, na=False) &
    df_expanded_filtered['검사결과'].str.contains(r'Vancomycin\s+\S+\s+\(R\)', regex=True, na=False),
    'EVAN(R)'
] = 1

# PSA 균주 (PSA == 1)에 대한 Imipenem(R) 및 Meropenem(R)
# Imipenem(R)
# df_combined 대신 df_expanded_filtered 사용
df_expanded_filtered.loc[
    (df_expanded_filtered['PSA'] == 1) &
    df_expanded_filtered['검사결과'].str.contains('Imipenem', case=False, na=False) &
    df_expanded_filtered['검사결과'].str.contains(r'Imipenem\s+\S+\s+\(R\)', regex=True, na=False),
    'PIMP(R)'
] = 1

# Meropenem(R)
# df_combined 대신 df_expanded_filtered 사용
df_expanded_filtered.loc[
    (df_expanded_filtered['PSA'] == 1) &
    df_expanded_filtered['검사결과'].str.contains('Meropenem', case=False, na=False) &
    df_expanded_filtered['검사결과'].str.contains(r'Meropenem\s+\S+\s+\(R\)', regex=True, na=False),
    'PMEM(R)'
] = 1

# ABA 균주 (ABA == 1)에 대한 Imipenem(R) 및 Meropenem(R)
# Imipenem(R)
# df_combined 대신 df_expanded_filtered 사용
df_expanded_filtered.loc[
    (df_expanded_filtered['ABA'] == 1) &
    df_expanded_filtered['검사결과'].str.contains('Imipenem', case=False, na=False) &
    df_expanded_filtered['검사결과'].str.contains(r'Imipenem\s+\S+\s+\(R\)', regex=True, na=False),
    'AIMP(R)'
] = 1

# Meropenem(R)
# df_combined 대신 df_expanded_filtered 사용
df_expanded_filtered.loc[
    (df_expanded_filtered['ABA'] == 1) &
    df_expanded_filtered['검사결과'].str.contains('Meropenem', case=False, na=False) &
    df_expanded_filtered['검사결과'].str.contains(r'Meropenem\s+\S+\s+\(R\)', regex=True, na=False),
    'AMEM(R)'
] = 1

# SAU 균주 (SAU == 1)에 대한 Oxacillin(R)
# df_combined 대신 df_expanded_filtered 사용
df_expanded_filtered.loc[
    (df_expanded_filtered['SAU'] == 1) &
    df_expanded_filtered['검사결과'].str.contains('Oxacillin', case=False, na=False) &
    df_expanded_filtered['검사결과'].str.contains(r'Oxacillin\s+\S+\s+\(R\)', regex=True, na=False),
    'OXA(R)'
] = 1

# SAU 균주 (SAU == 1)에 대한 Vancomycin(R)인 경우 SVAN(R) 추가
# df_combined 대신 df_expanded_filtered 사용
df_expanded_filtered.loc[
    (df_expanded_filtered['SAU'] == 1) &
    df_expanded_filtered['검사결과'].str.contains('Vancomycin', case=False, na=False) &
    df_expanded_filtered['검사결과'].str.contains(r'Vancomycin\s+\S+\s+\(R\)', regex=True, na=False),
    'SVAN(R)'
] = 1

# CRE 균주 (CRE == 1)에 대한 Imipenem(R) 및 Meropenem(R) 및 Ertapenem(R)
# Imipenem(R)
# df_combined 대신 df_expanded_filtered 사용
df_expanded_filtered.loc[
    (df_expanded_filtered['CRE'] == 1) &
    df_expanded_filtered['검사결과'].str.contains('Imipenem', case=False, na=False) &
    df_expanded_filtered['검사결과'].str.contains(r'Imipenem\s+\S+\s+\(R\)', regex=True, na=False),
    'CIMP(R)'
] = 1

# Meropenem(R)
# df_combined 대신 df_expanded_filtered 사용
df_expanded_filtered.loc[
    (df_expanded_filtered['CRE'] == 1) &
    df_expanded_filtered['검사결과'].str.contains('Meropenem', case=False, na=False) &
    df_expanded_filtered['검사결과'].str.contains(r'Meropenem\s+\S+\s+\(R\)', regex=True, na=False),
    'CMEM(R)'
] = 1

# Ertapenem(R)
# df_combined 대신 df_expanded_filtered 사용
df_expanded_filtered.loc[
    (df_expanded_filtered['CRE'] == 1) &
    df_expanded_filtered['검사결과'].str.contains('Ertapenem', case=False, na=False) &
    df_expanded_filtered['검사결과'].str.contains(r'Ertapenem\s+\S+\s+\(R\)', regex=True, na=False),
    'CETP(R)'
] = 1

print("\n--- 3. 항생제 내성 약어 컬럼 생성 완료 (균주명 연동) ---")
print("생성된 내성 컬럼 목록:", new_resistance_cols)








# --- 9. 컬럼 리스트 및 추가된 컬럼 건수 확인 ---
print("\n--- 4. 생성된 약어 컬럼별 '1'의 개수 ---")

# 균주명 약어 컬럼
organism_abbr_cols = ['EFU', 'EFA', 'PSA', 'ABA', 'SAU', 'CRE']
# df_combined 대신 df_expanded_filtered 사용
for col in organism_abbr_cols:
    if col in df_expanded_filtered.columns:
        count = df_expanded_filtered[col].sum()
        print(f"'{col}' 컬럼에서 1의 개수: {int(count)}")
    else:
        print(f"경고: '{col}' 컬럼을 찾을 수 없습니다.")

# 항생제 내성 약어 컬럼
resistance_abbr_cols = ['EVAN(R)', 'PIMP(R)', 'PMEM(R)', 'AIMP(R)', 'AMEM(R)', 'OXA(R)', 'SVAN(R)']
# df_combined 대신 df_expanded_filtered 사용
for col in resistance_abbr_cols:
    if col in df_expanded_filtered.columns:
        count = df_expanded_filtered[col].sum()
        print(f"'{col}' 컬럼에서 1의 개수: {int(count)}")
    else:
        print(f"경고: '{col}' 컬럼을 찾을 수 없습니다.")

print("\n--- 1의 개수 카운트 완료 ---")








# --- 10. 최종 데이터 확정 및 저장 ---
# 최종 데이터프레임으로 df_expanded_filtered를 사용
df_final = df_expanded_filtered

print("\n--- 5. 최종 데이터 확정 (모든 약어 컬럼 적용) ---")
print("최종 데이터프레임의 상위 5행:")
print(df_final.head())
print(f"최종 데이터프레임의 총 행 수: {len(df_final)} 행")
print(f"최종 데이터프레임의 컬럼 목록: {df_final.columns.tolist()}")

# 최종 데이터를 엑셀 파일로 저장
output_file_name = '내부데이터_전처리_최종(FirstIsolation 전).xlsx'
try:
    df_final.to_excel(output_file_name, index=False)
    print(f"\n성공적으로 '{output_file_name}' 파일로 저장되었습니다.")
except Exception as e:
    print(f"\n오류: 엑셀 파일 저장 중 오류 발생: {e}")

print("\n스크립트 실행 완료.")
