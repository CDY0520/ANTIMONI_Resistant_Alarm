# 라이브러리 임포트
import pandas as pd
import os

# 엑셀 파일 경로
file_path = 'C:/kdtcb_learn/내부데이터_전처리_최종(FirstIsolation 전).xlsx'

# --- pandas 출력 설정 변경: 모든 행을 출력하도록 설정 ---
pd.set_option('display.max_rows', None) # 모든 행을 출력
pd.set_option('display.max_columns', None) # 모든 컬럼을 출력
pd.set_option('display.width', 1000) # 출력 너비 설정 (잘림 방지)
print(f"--- '{file_path}'에서 표본감시 건수 세기 시작 ---")

if not os.path.exists(file_path):
    print(f"오류: 파일을 찾을 수 없습니다 - {file_path}")
else:
    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(file_path)
        print(f"파일 불러오기 성공. 총 {len(df)} 행.")

        # 필요한 공통 컬럼 ('검사시행일자', '환자번호', '검체명(주검체)')이 존재하는지 확인
        common_required_cols = ['검사시행일자', '환자번호', '검체명(주검체)'] # '검체명(주검체)' 추가
        for col in common_required_cols:
            if col not in df.columns:
                print(f"오류: 필수 컬럼 '{col}'을(를) 찾을 수 없습니다. 엑셀 파일의 컬럼 이름을 확인해주세요.")
                exit() # 필수 컬럼이 없으면 종료

        # '검사시행일자' 컬럼을 datetime 형식으로 변환
        df['검사시행일자'] = pd.to_datetime(df['검사시행일자'], errors='coerce')

        # 검사시행일자가 NaT인 경우는 제외
        df.dropna(subset=['검사시행일자'], inplace=True)

        # '검사시행일자'를 기준으로 '년월' 컬럼 생성 (월 단위)
        df['년월'] = df['검사시행일자'].dt.to_period('M')

        # 각 감염병 유형별 First Isolation 데이터프레임을 저장할 딕셔너리
        first_isolation_dfs = {}

        # --- VRE (EVAN(R)) First Isolation 데이터 처리 ---
        print("\n========== VRE (EVAN(R)) First Isolation 데이터 처리 시작 ==========")
        vre_required_cols = ['EVAN(R)']
        if not all(col in df.columns for col in vre_required_cols):
            print(f"오류: VRE 분석을 위한 필수 컬럼 중 하나 이상이 없습니다: {vre_required_cols}. 엑셀 파일의 컬럼 이름을 확인해주세요.") #
            first_isolation_dfs['VRE'] = pd.DataFrame() # 빈 데이터프레임 할당
            print("VRE 분석을 건너e띄니다.")
        else:
            df_vre_only = df[df['EVAN(R)'] == 1].copy() #
            if df_vre_only.empty:
                print("경고: 'EVAN(R)' 컬럼 값이 1인 데이터가 없어 VRE First Isolation을 수행할 수 없습니다.") #
                first_isolation_dfs['VRE'] = pd.DataFrame()
            else:
                print(f"'EVAN(R)'이 1인 원본 데이터 수: {len(df_vre_only)} 행")
                # Groupby에 '검체명(주검체)' 추가
                df_vre_first_isolation = df_vre_only.sort_values(by='검사시행일자').groupby(
                    ['환자번호', '검체명(주검체)', '년월'], as_index=False # '검체명(주검체)' 추가
                ).first()
                first_isolation_dfs['VRE'] = df_vre_first_isolation
                print(f"VRE(EVAN(R)) First Isolation 적용 후 데이터 수: {len(df_vre_first_isolation)} 행")
                print("VRE(EVAN(R)) First Isolation 적용 후 데이터프레임의 상위 5행:")
                print(df_vre_first_isolation[['환자번호', '검체명(주검체)', '년월', '검사시행일자', 'EVAN(R)']].head()) #
                print(f"\n--- 월별 VRE(EVAN(R)) First Isolation 건수 ---")
                monthly_vre_counts = df_vre_first_isolation['년월'].value_counts().sort_index()
                print(monthly_vre_counts)
                print(f"\n총 VRE(EVAN(R)) First Isolation 건수: {len(df_vre_first_isolation)} 건")


        # --- MRPA (PIMP(R) 또는 PMEM(R)) First Isolation 데이터 처리 ---
        print("\n========== MRPA (PIMP(R) 또는 PMEM(R)) First Isolation 데이터 처리 시작 ==========")
        mrpa_required_cols = ['PIMP(R)', 'PMEM(R)']
        if not all(col in df.columns for col in mrpa_required_cols):
            print(f"오류: MRPA 분석을 위한 필수 컬럼 중 하나 이상이 없습니다: {mrpa_required_cols}. 엑셀 파일의 컬럼 이름을 확인해주세요.") #
            first_isolation_dfs['MRPA'] = pd.DataFrame()
            print("MRPA 분석을 건너뜁니다.")
        else:
            df_mrpa_only = df[((df['PIMP(R)'] == 1) | (df['PMEM(R)'] == 1))].copy() #
            if df_mrpa_only.empty:
                print("경고: 'PIMP(R)' 또는 'PMEM(R)' 컬럼 값이 1인 데이터가 없어 MRPA First Isolation을 수행할 수 없습니다.") #
                first_isolation_dfs['MRPA'] = pd.DataFrame()
            else:
                print(f"MRPA 관련 원본 데이터 수: {len(df_mrpa_only)} 행")
                # Groupby에 '검체명(주검체)' 추가
                df_mrpa_first_isolation = df_mrpa_only.sort_values(by='검사시행일자').groupby(
                    ['환자번호', '검체명(주검체)', '년월'], as_index=False # '검체명(주검체)' 추가
                ).first()
                first_isolation_dfs['MRPA'] = df_mrpa_first_isolation
                print(f"MRPA First Isolation 적용 후 데이터 수: {len(df_mrpa_first_isolation)} 행")
                print("MRPA First Isolation 적용 후 데이터프레임의 상위 5행:")
                print(df_mrpa_first_isolation[['환자번호', '검체명(주검체)', '년월', '검사시행일자', 'PIMP(R)', 'PMEM(R)']].head()) #
                print(f"\n--- 월별 MRPA First Isolation 건수 ---")
                monthly_mrpa_counts = df_mrpa_first_isolation['년월'].value_counts().sort_index()
                print(monthly_mrpa_counts)
                print(f"\n총 MRPA First Isolation 건수: {len(df_mrpa_first_isolation)} 건")


        # --- MRAB (AIMP(R) 또는 AMEM(R)) First Isolation 데이터 처리 ---
        print("\n========== MRAB (AIMP(R) 또는 AMEM(R)) First Isolation 데이터 처리 시작 ==========")
        mrab_required_cols = ['AIMP(R)', 'AMEM(R)']
        if not all(col in df.columns for col in mrab_required_cols):
            print(f"오류: MRAB 분석을 위한 필수 컬럼 중 하나 이상이 없습니다: {mrab_required_cols}. 엑셀 파일의 컬럼 이름을 확인해주세요.") #
            first_isolation_dfs['MRAB'] = pd.DataFrame()
            print("MRAB 분석을 건너뜁니다.")
        else:
            df_mrab_only = df[((df['AIMP(R)'] == 1) | (df['AMEM(R)'] == 1))].copy() #
            if df_mrab_only.empty:
                print("경고: 'AIMP(R)' 또는 'AMEM(R)' 컬럼 값이 1인 데이터가 없어 MRAB First Isolation을 수행할 수 없습니다.") #
                first_isolation_dfs['MRAB'] = pd.DataFrame()
            else:
                print(f"MRAB 관련 원본 데이터 수: {len(df_mrab_only)} 행")
                # Groupby에 '검체명(주검체)' 추가
                df_mrab_first_isolation = df_mrab_only.sort_values(by='검사시행일자').groupby(
                    ['환자번호', '검체명(주검체)', '년월'], as_index=False # '검체명(주검체)' 추가
                ).first()
                first_isolation_dfs['MRAB'] = df_mrab_first_isolation
                print(f"MRAB First Isolation 적용 후 데이터 수: {len(df_mrab_first_isolation)} 행")
                print("MRAB First Isolation 적용 후 데이터프레임의 상위 5행:")
                print(df_mrab_first_isolation[['환자번호', '검체명(주검체)', '년월', '검사시행일자', 'AIMP(R)', 'AMEM(R)']].head()) #
                print(f"\n--- 월별 MRAB First Isolation 건수 ---")
                monthly_mrab_counts = df_mrab_first_isolation['년월'].value_counts().sort_index()
                print(monthly_mrab_counts)
                print(f"\n총 MRAB First Isolation 건수: {len(df_mrab_first_isolation)} 건")


        # --- MRSA (OXA(R)) First Isolation 데이터 처리 ---
        print("\n========== MRSA (OXA(R)) First Isolation 데이터 처리 시작 ==========")
        mrsa_required_cols = ['OXA(R)']
        if not all(col in df.columns for col in mrsa_required_cols):
            print(f"오류: MRSA 분석을 위한 필수 컬럼 중 하나 이상이 없습니다: {mrsa_required_cols}. 엑셀 파일의 컬럼 이름을 확인해주세요.") #
            first_isolation_dfs['MRSA'] = pd.DataFrame()
            print("MRSA 분석을 건너킵니다.")
        else:
            df_mrsa_only = df[df['OXA(R)'] == 1].copy() #
            if df_mrsa_only.empty:
                print("경고: 'OXA(R)' 컬럼 값이 1인 데이터가 없어 MRSA First Isolation을 수행할 수 없습니다.") #
                first_isolation_dfs['MRSA'] = pd.DataFrame()
            else:
                print(f"'OXA(R)'이 1인 원본 데이터 수: {len(df_mrsa_only)} 행")
                # Groupby에 '검체명(주검체)' 추가
                df_mrsa_first_isolation = df_mrsa_only.sort_values(by='검사시행일자').groupby(
                    ['환자번호', '검체명(주검체)', '년월'], as_index=False # '검체명(주검체)' 추가
                ).first()
                first_isolation_dfs['MRSA'] = df_mrsa_first_isolation
                print(f"MRSA First Isolation 적용 후 데이터 수: {len(df_mrsa_first_isolation)} 행")
                print("MRSA First Isolation 적용 후 데이터프레임의 상위 5행:")
                print(df_mrsa_first_isolation[['환자번호', '검체명(주검체)', '년월', '검사시행일자', 'OXA(R)']].head()) #
                print(f"\n--- 월별 MRSA (OXA(R)) First Isolation 건수 ---")
                monthly_mrsa_counts = df_mrsa_first_isolation['년월'].value_counts().sort_index()
                print(monthly_mrsa_counts)
                print(f"\n총 MRSA (OXA(R)) First Isolation 건수: {len(df_mrsa_first_isolation)} 건")


        # --- 모든 표본감시 감염병의 월별 First Isolation 건수 합계 ---
        print("\n========== 월별 의료관련감염병 (표본감시) 건수 합계 ==========")

        # 각 감염병별 월별 건수를 Series로 가져오기 (없으면 빈 Series)
        # 여기서 각 first_isolation_dfs[key]는 환자번호, 검체명(주검체), 년월로 그룹화된 데이터프레임입니다.
        # 각 월별 카운트를 위해서는 '년월' 컬럼의 value_counts를 다시 사용합니다.
        vre_counts_series = first_isolation_dfs['VRE']['년월'].value_counts().sort_index() if not first_isolation_dfs['VRE'].empty else pd.Series(dtype=int) #
        mrpa_counts_series = first_isolation_dfs['MRPA']['년월'].value_counts().sort_index() if not first_isolation_dfs['MRPA'].empty else pd.Series(dtype=int) #
        mrab_counts_series = first_isolation_dfs['MRAB']['년월'].value_counts().sort_index() if not first_isolation_dfs['MRAB'].empty else pd.Series(dtype=int) #
        mrsa_counts_series = first_isolation_dfs['MRSA']['년월'].value_counts().sort_index() if not first_isolation_dfs['MRSA'].empty else pd.Series(dtype=int) #

        # 모든 Series를 하나의 DataFrame으로 합치기
        # fill_value=0을 사용하여 누락된 월은 0으로 채움
        combined_monthly_counts = pd.DataFrame({
            'VRE': vre_counts_series,
            'MRPA': mrpa_counts_series,
            'MRAB': mrab_counts_series,
            'MRSA': mrsa_counts_series
        }).fillna(0).astype(int) # NaN 값을 0으로 채우고 정수형으로 변환

        # '표본감시' 컬럼 (총합) 생성
        combined_monthly_counts['표본감시'] = combined_monthly_counts[['VRE', 'MRPA', 'MRAB', 'MRSA']].sum(axis=1)

        # 년월 기준으로 정렬
        combined_monthly_counts = combined_monthly_counts.sort_index()

        print("\n--- 월별 표본감시 감염볍 건수 요약 ---")
        print(combined_monthly_counts)

        # --- 최종 결과 엑셀 파일로 저장 ---
        output_combined_file_name = '월별_표본감시_건수.xlsx'
        print(f"\n========== 월별 표본감시 감염병 건수 엑셀 파일 저장 시작 ==========")
        try:
            combined_monthly_counts.to_excel(output_combined_file_name, index=True) # 년월을 인덱스로 저장
            print(f"성공적으로 '{output_combined_file_name}' 파일로 저장되었습니다.")
        except Exception as e:
            print(f"오류: 엑셀 파일 저장 중 오류 발생: {e}")

    except Exception as e:
        print(f"파일 처리 중 오류 발생: {e}")

print("\n--- 표본감시 감염병 건수 세기 완료 ---")