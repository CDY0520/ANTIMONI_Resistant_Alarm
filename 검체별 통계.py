import pandas as pd

# 1. 엑셀 파일 로드 (파일 경로와 이름 확인)
file_name = '내부데이터_전처리_최종(FirstIsolation 전).xlsx'
try:
    df = pd.read_excel(file_name)
    print(f"'{file_name}' 파일이 성공적으로 로드되었습니다.")
except FileNotFoundError:
    print(f"오류: '{file_name}' 파일을 찾을 수 없습니다. 파일 경로와 이름을 확인해주세요.")
    exit() # 파일이 없으면 스크립트 종료

# 2. '검사시행일자'를 datetime 형식으로 변환하고 연도 컬럼 생성
df['검사시행일자'] = pd.to_datetime(df['검사시행일자'], errors='coerce')

# 날짜 변환 중 오류가 발생하여 '검사시행일자'가 NaT이 된 행은 분석에서 제외합니다.
df.dropna(subset=['검사시행일자'], inplace=True)
df['검사시행연도'] = df['검사시행일자'].dt.year.astype(int) # 연도를 정수형으로 변환


# 3. 그룹화 및 조건부 카운트를 위한 전처리
# '환자번호', '검체명(주검체)', '균주명', '검사시행연도' 기준으로 정렬 후
# 이 4가지 컬럼이 같으면
# 가장 빠른 '검사시행일자'를 가진 행만 남기고 나머지는 제거
# (즉, 동일 환자번호, 동일 검체명, 동일 균주가 동일 연도에 여러 번 검출되어도 첫 번째 기록만 유효)
df_filtered = df.sort_values(by=['환자번호', '검체명(주검체)', '균주명', '검사시행연도', '검사시행일자']).drop_duplicates(
    subset=['환자번호', '검체명(주검체)', '균주명', '검사시행연도'], # 환자번호 포함
    keep='first'
)

# 4. 필터링된 데이터에서 '검사시행연도', '검체명(주검체)', '균주명' 별로 균주명 카운트
# '검사시행연도'를 groupby 키에 포함시켜 결과 테이블에 연도가 나타나도록 합니다.
grouped_result = df_filtered.groupby(['검사시행연도', '검체명(주검체)', '균주명']).size().reset_index(name='카운트')

# --- 변경된 부분: '카운트' 컬럼만 기준으로 내림차순 정렬 ---
# 다른 정렬 기준 없이 오직 '카운트'만 가지고 내림차순 정렬합니다.
grouped_result = grouped_result.sort_values(
    by='카운트',
    ascending=False
)
# ----------------------------------------------------

print("\n연도별, 검체명(주검체)별, 균주명별 유효 카운트 (카운트 내림차순 정렬):")
print(grouped_result)

# 5. 결과를 CSV 파일로 저장
output_csv_file = '연별_검체명_균주명_카운트_결과.csv'
grouped_result.to_csv(output_csv_file, index=False, encoding='utf-8-sig') # 한글 깨짐 방지를 위해 'utf-8-sig' 인코딩 사용
print(f"\n분석 결과가 '{output_csv_file}' 파일로 성공적으로 저장되었습니다.")

# 최종 필터링된 데이터프레임 확인 (필요시)
print("\n최종 필터링된 데이터 (각 그룹/연도별 첫 번째 기록):")
print(df_filtered.head())