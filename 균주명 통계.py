# 라이브러리 임포트
import pandas as pd

# 1. csv 파일 로드
file_name = '연별_검체명_균주명_카운트_결과.csv'
try:
    df_loaded = pd.read_csv(file_name, encoding='utf-8-sig')
    print(f"'{file_name}' 파일이 성공적으로 로드되었습니다.")
except FileNotFoundError:
    print(f"오류: '{file_name}' 파일을 찾을 수 없습니다. 파일 경로와 이름을 확인해주세요.")
    exit() # 파일이 없으면 스크립트 종료

# 로드된 데이터프레임의 컬럼명 확인
print("\n로드된 데이터프레임의 컬럼:")
print(df_loaded.columns)
print("\n로드된 데이터프레임 미리보기:")
print(df_loaded.head())

# 2. '검사시행연도'와 '균주명'으로 그룹화하여 '카운트'의 합계 계산
# '검체명(주검체)'는 그룹화 기준에서 제외하여 전체 합계를 구합니다.
yearly_bacterium_total_count = df_loaded.groupby(['검사시행연도', '균주명'])['카운트'].sum().reset_index()

# 3. 결과를 '카운트' 기준으로 내림차순 정렬 (선택 사항: 연도도 함께 정렬 가능)
# 여기서는 '검사시행연도'는 오름차순으로, 각 연도 내에서는 '카운트'를 내림차순으로 정렬합니다.
yearly_bacterium_total_count = yearly_bacterium_total_count.sort_values(
    by=['검사시행연도', '카운트'],
    ascending=[True, False] # 연도는 오름차순, 카운트는 내림차순
)

print("\n연도별, 균주명별 전체 카운트 합계 (내림차순 정렬):")
print(yearly_bacterium_total_count)

# 4. 결과를 새로운 CSV 파일로 저장
output_csv_file = '연도별_균주명_카운트.csv'
yearly_bacterium_total_count.to_csv(output_csv_file, index=False, encoding='utf-8-sig') # 한글 깨짐 방지를 위해 'utf-8-sig' 인코딩 사용
print(f"\n분석 결과가 '{output_csv_file}' 파일로 성공적으로 저장되었습니다.")