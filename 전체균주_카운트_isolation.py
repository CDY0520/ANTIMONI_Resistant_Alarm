# 라이브러리 임포트
import pandas as pd
import os

# 엑셀 파일 경로
file_path = 'C:/kdtcb_learn/내부데이터_전처리_최종(FirstIsolation 전).xlsx' # <-- 엑셀 파일의 정확한 경로를 입력해주세요.

# --- pandas 출력 설정 변경: 모든 행을 출력하도록 설정 ---
pd.set_option('display.max_rows', None)    # 모든 행을 출력
pd.set_option('display.max_columns', None) # 모든 컬럼을 출력
pd.set_option('display.width', 1000)       # 출력 너비 설정 (잘림 방지)

print(f"--- '{file_path}'에서 균주명 상위 20개 건수 세기 시작 ---")

if not os.path.exists(file_path):
    print(f"오류: 파일을 찾을 수 없습니다 - {file_path}")
else:
    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(file_path)
        print(f"파일 불러오기 성공. 총 {len(df)} 행.")

        # 필요한 컬럼이 존재하는지 확인
        required_cols = ['환자번호', '검사시행일자', '검체명(주검체)', '균주명'] #
        for col in required_cols:
            if col not in df.columns:
                print(f"오류: 필수 컬럼 '{col}'을(를) 찾을 수 없습니다. 엑셀 파일의 컬럼 이름을 확인해주세요.") #
                exit() # 필수 컬럼이 없으면 종료

        # '검사시행일자' 컬럼을 datetime 형식으로 변환
        df['검사시행일자'] = pd.to_datetime(df['검사시행일자'], errors='coerce') #

        # 검사시행일자가 NaT인 경우는 제외
        df.dropna(subset=['검사시행일자'], inplace=True) #

        # '균주명' 컬럼에 NaN 값이 있으면 제거 (분석 대상에서 제외)
        df.dropna(subset=['균주명'], inplace=True)

        # '균주명'에서 공백 제거 (일관성을 위해)
        df['균주명'] = df['균주명'].str.strip()

        # 데이터프레임이 비어있는지 다시 확인
        if df.empty:
            print("처리할 유효한 균주명 데이터가 없습니다.")
        else:
            print(f"유효한 '균주명' 데이터 수: {len(df)} 행")

            # First Isolation 로직 적용: 환자번호, 검체명(주검체), 균주명 별로 월별만 제외하고 첫 데이터 카운트
            # '검사시행일자'로 먼저 정렬하여 가장 빠른 날짜의 데이터가 first()로 선택되게 함
            df_first_isolation_species = df.sort_values(by='검사시행일자').groupby(
                ['환자번호', '검체명(주검체)', '균주명'], as_index=False #
            ).first() #

            print(f"\nFirst Isolation 적용 후 데이터 수 (환자-검체-균주별 첫 분리): {len(df_first_isolation_species)} 행")
            print("First Isolation 적용 후 데이터프레임의 상위 5행:")
            print(df_first_isolation_species[['환자번호', '검체명(주검체)', '균주명', '검사시행일자']].head())

            # 균주명별 건수 집계
            species_counts = df_first_isolation_species['균주명'].value_counts() #

            # 상위 20개 균주 건수 출력
            print("\n========== 상위 20개 균주명별 건수 (First Isolation 기준) ==========")
            if not species_counts.empty:
                print(species_counts.head(20).to_string()) #
            else:
                print("집계할 균주 데이터가 없습니다.")

    except Exception as e:
        print(f"파일 처리 중 오류 발생: {e}")

print("\n--- 균주명 상위 20개 건수 세기 완료 ---")