import pandas as pd
import re

# 1. 엑셀 파일 로드 (파일 경로와 이름 확인)
file_name = '내부데이터_전처리_최종(FirstIsolation 전).xlsx'
try:
    original = pd.read_excel(file_name)
    print(f"'{file_name}' 파일이 성공적으로 로드되었습니다.")
except FileNotFoundError:
    print(f"오류: '{file_name}' 파일을 찾을 수 없습니다. 파일 경로와 이름을 확인해주세요.")
    exit()

# 2. 필요한 컬럼 추출 후 데이터 구성
columns_to_select = ['환자번호', '검사시행일자', '검체명(주검체)', '검사결과', '균주명']
try:
    df_selected = original[columns_to_select].copy()
    print(f"\n'{columns_to_select}' 컬럼들로 새로운 데이터프레임이 구성되었습니다.")
    print("\n새로운 데이터프레임 미리보기:")
    print(df_selected.head())
except KeyError as e:
    print(f"\n오류: 컬럼 선택 중 문제가 발생했습니다. '{e}' 컬럼을 찾을 수 없습니다.")
    print("엑셀 파일의 정확한 컬럼 이름을 'columns_to_select' 리스트에 입력했는지 확인해주세요.")
    print("현재 엑셀 파일에 있는 컬럼들은 다음과 같습니다:", original.columns.tolist())
    exit()

# 3. 타겟 균주 필터링 및 First Isolation 로직 적용
# '균주명'이 'Escherichia coli'인 것만 필터링
TARGET_BUG_NAME = 'Escherichia coli'  # 균주명 변수
TARGET_BUG_ABBREVIATION = 'E.coli'  # 약어 변수 (설명 및 파일 이름용)

df_bug = df_selected[df_selected['균주명'] == TARGET_BUG_NAME].copy()
print(f"\n'{TARGET_BUG_NAME}'만 필터링된 데이터프레임 미리보기:")
print(df_bug.head())

# '검사시행일자'를 datetime 형식으로 변환하고 연도 컬럼 생성
df_bug['검사시행일자'] = pd.to_datetime(df_bug['검사시행일자'], errors='coerce')

# 날짜 변환 중 오류가 발생하여 '검사시행일자'가 NaT이 된 행은 분석에서 제외합니다.
df_bug.dropna(subset=['검사시행일자'], inplace=True)
df_bug['검사시행연도'] = df_bug['검사시행일자'].dt.year.astype(int)  # 연도를 정수형으로 변환

# 환자번호별, 검체명(주검체)별, 연도별로 묶어서 가장 처음 날짜만 카운트될 데이터프레임 생성
# 이 데이터프레임의 각 행은 특정 환자의 특정 검체에서 특정 연도에 타겟 균주가 처음 분리된 것을 의미합니다.
df_bug = df_bug.sort_values(by=['환자번호', '검체명(주검체)', '검사시행연도', '검사시행일자']).drop_duplicates(
    subset=['환자번호', '검체명(주검체)', '검사시행연도'],
    keep='first'
)

print(f"\n최종 필터링 및 First Isolation 적용된 {TARGET_BUG_NAME} 데이터프레임 미리보기:")
print(df_bug.head())
print(f"\n최종 {TARGET_BUG_NAME} 데이터프레임의 총 행 수: {len(df_bug)}")


# --- 4. 검사결과 파싱하여 항생제별 S, I, R 컬럼 생성 (동적으로 컬럼 생성) ---

# 항생제 감수성 결과 파싱 함수
def parse_antibiotic_results_to_dict(result_string):
    results = {}
    if pd.isna(result_string):
        return results  # NaN 값이면 빈 딕셔너리 반환

    감수성결과_문자열 = str(result_string)

    # "항생제 감수성결과" 이후의 내용만 추출하거나, 없다면 "동정결과" 부분을 제거
    match_감수성결과_시작 = re.search(r'항생제 감수성결과\s*(.*)', 감수성결과_문자열, re.DOTALL)
    if match_감수성결과_시작:
        parse_target_string = match_감수성결과_시작.group(1).strip()
    else:
        parse_target_string = re.sub(r'동정결과:\s*[^;]+?(?:;|$)\s*', '', 감수성결과_문자열, flags=re.DOTALL).strip()

    if not parse_target_string:
        return results

    # 정규표현식: 항생제 이름 (영문, 슬래시, 하이픈, 공백 포함)을 찾고, 그 뒤의 판정 (S/I/R/+)을 찾습니다.
    # 특정 약어에 대한 특별 처리 없이, 일반적인 영단어 패턴만 따릅니다.
    matches = re.findall(r'([A-Za-z/\-\s]+)\s*:\s*(?:[^()]*?)\(([SIR\+])\)', parse_target_string, re.DOTALL)

    for abx, res in matches:
        abx_clean = abx.strip()
        # 약어를 정식 명칭으로 통일하는 로직이 없습니다.
        results[abx_clean] = res.strip()

    # ESBL 특수 처리: 'ESBL : Pos (+)' 또는 'ESBL : (+)'
    match_esbl = re.search(r'ESBL\s*:\s*(?:Pos\s*)?\(([+])\)', parse_target_string, re.DOTALL)
    if match_esbl:
        results['ESBL'] = match_esbl.group(1)

    return results


# '검사결과' 컬럼을 파싱하여 항생제별 결과를 딕셔너리로 만듭니다.
parsed_antibiotic_data_series = df_bug['검사결과'].apply(parse_antibiotic_results_to_dict)

# --- all_unique_antibiotic_columns를 동적으로 수집 ---
all_unique_antibiotic_columns = set()
for item_dict in parsed_antibiotic_data_series:
    for abx, result in item_dict.items():
        if abx == 'ESBL' and result == '+':
            all_unique_antibiotic_columns.add('ESBL(+)')
        elif result in ['S', 'I', 'R']:
            all_unique_antibiotic_columns.add(f'{abx}({result})')

# 새로운 컬럼들을 0으로 초기화
for col_name in all_unique_antibiotic_columns:
    df_bug[col_name] = 0

# 각 행을 순회하며 해당하는 항생제 컬럼에 1을 채웁니다.
for index, parsed_dict in parsed_antibiotic_data_series.items():
    for abx, result in parsed_dict.items():
        col_to_set = None
        if abx == 'ESBL' and result == '+':
            col_to_set = 'ESBL(+)'
        elif result in ['S', 'I', 'R']:
            col_to_set = f'{abx}({result})'

        if col_to_set and col_to_set in df_bug.columns:
            df_bug.at[index, col_to_set] = 1

# '검사결과' 컬럼은 더 이상 필요 없으므로 제거 (선택 사항)
# df_bug.drop(columns=['검사결과'], inplace=True)

print(f"\n--- 항생제별 S/I/R 컬럼이 추가된 {TARGET_BUG_NAME} 데이터프레임 미리보기 (새로운 컬럼 포함) ---")
print(f"새로운 {TARGET_BUG_NAME} 데이터프레임의 총 컬럼 수: {len(df_bug.columns)}")
print("생성된 모든 컬럼 목록:")
print(df_bug.columns.tolist())

# Pandas 출력 옵션 설정
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

print(f"\n새로운 {TARGET_BUG_NAME} 데이터프레임 미리보기 (모든 컬럼 포함 시도):")
print(df_bug.head())

print(f"\n새롭게 생성된 항생제 관련 컬럼 수: {len(all_unique_antibiotic_columns)}")

# --- 5. 항생제별 전체 카운트 및 S, I, R 비율 계산 ---

# 통계를 낼 항생제 목록을 동적으로 생성
summary_antibiotic_names = set()
for col_name in all_unique_antibiotic_columns:
    if col_name.endswith('(+)'):  # ESBL(+)
        summary_antibiotic_names.add(col_name[:-3])  # ESBL
    elif col_name.endswith('(S)') or col_name.endswith('(I)') or col_name.endswith('(R)'):
        match = re.match(r'(.+?)\([SIR]\)', col_name)
        if match:
            summary_antibiotic_names.add(match.group(1).strip())

summary_antibiotic_list = sorted(list(summary_antibiotic_names))

# 결과를 저장할 빈 리스트
antibiotic_summary_data = []

# 각 항생제 이름을 기준으로 카운트 및 비율 계산
for abx_name in summary_antibiotic_list:
    s_col = f'{abx_name}(S)'
    i_col = f'{abx_name}(I)'
    r_col = f'{abx_name}(R)'
    esbl_plus_col = 'ESBL(+)'

    s_count = df_bug[s_col].sum() if s_col in df_bug.columns else 0
    i_count = df_bug[i_col].sum() if i_col in df_bug.columns else 0
    r_count = df_bug[r_col].sum() if r_col in df_bug.columns else 0

    if abx_name == 'ESBL':
        total_count = df_bug[esbl_plus_col].sum() if esbl_plus_col in df_bug.columns else 0
        s_ratio = 0
        i_ratio = 0
        r_ratio = 0
        antibiotic_summary_data.append({
            '항생제명': abx_name,
            '총 카운트': total_count,
            'S 카운트': s_count,
            'I 카운트': i_count,
            'R 카운트': r_count,
            'S 비율 (%)': s_ratio,
            'I 비율 (%)': i_ratio,
            'R 비율 (%)': r_ratio
        })
    else:
        total_count = s_count + i_count + r_count

        s_ratio = (s_count / total_count * 100) if total_count > 0 else 0
        i_ratio = (i_count / total_count * 100) if total_count > 0 else 0
        r_ratio = (r_count / total_count * 100) if total_count > 0 else 0

        antibiotic_summary_data.append({
            '항생제명': abx_name,
            '총 카운트': total_count,
            'S 카운트': s_count,
            'I 카운트': i_count,
            'R 카운트': r_count,
            'S 비율 (%)': s_ratio,
            'I 비율 (%)': i_ratio,
            'R 비율 (%)': r_ratio
        })

# 결과를 DataFrame으로 변환
df_final_antibiotic_summary = pd.DataFrame(antibiotic_summary_data)

# '총 카운트' 기준으로 내림차순 정렬
df_final_antibiotic_summary = pd.DataFrame(antibiotic_summary_data).sort_values(by='총 카운트', ascending=False)

print("\n--- 최종 항생제 감수성 통계 (카운트 및 비율) ---")
print(df_final_antibiotic_summary)

# 6. 통계 결과를 CSV 파일로 저장
output_final_summary_csv_file = 'Ecoli_항생제감수성_통계.csv' # 파일 이름 변경
df_final_antibiotic_summary.to_csv(output_final_summary_csv_file, index=False, encoding='utf-8-sig')
print(f"\n최종 항생제 감수성 통계 결과가 '{output_final_summary_csv_file}' 파일로 성공적으로 저장되었습니다.")