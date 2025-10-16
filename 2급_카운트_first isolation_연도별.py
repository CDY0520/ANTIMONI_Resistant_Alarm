import pandas as pd
import os

# 엑셀 파일 경로
file_path = 'C:/kdtcb_learn/내부데이터_전처리_최종(FirstIsolation 전).xlsx'

# --- pandas 출력 설정 변경: 모든 행을 출력하도록 설정 ---
pd.set_option('display.max_rows', None)  # 모든 행을 출력
pd.set_option('display.max_columns', None)  # 모든 컬럼을 출력
pd.set_option('display.width', 1000)  # 출력 너비 설정 (잘림 방지)

print(f"--- '{file_path}'에서 2급감염병 건수 세기 시작 ---")

if not os.path.exists(file_path):
    print(f"오류: 파일을 찾을 수 없습니다 - {file_path}")
else:
    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(file_path)
        print(f"파일 불러오기 성공. 총 {len(df)} 행.")

        # 필요한 공통 컬럼 ('검사시행일자', '환자번호', '검체명(주검체)', 'SVAN(R)')이 존재하는지 확인
        # CRE 관련 컬럼은 이제 직접 생성하므로 필수 컬럼 목록에서 제외
        common_required_cols = ['검사시행일자', '환자번호', '검체명(주검체)', 'SVAN(R)']
        # 새로운 CRE(R) 생성을 위한 원본 컬럼 확인
        cre_source_cols = ['CIMP(R)', 'CMEM(R)', 'CETP(R)']

        for col in common_required_cols + cre_source_cols:
            if col not in df.columns:
                print(f"오류: 필수 컬럼 '{col}'을(를) 찾을 수 없습니다. 엑셀 파일의 컬럼 이름을 확인해주세요.")
                exit()  # 필수 컬럼이 없으면 종료

        # --- 새로운 CRE(R) 컬럼 생성 로직 추가 ---
        # CIMP(R), CMEM(R), CETP(R) 중 하나라도 1이면 CRE(R)을 1로, 아니면 0으로 설정
        # df[cre_source_cols].any(axis=1)은 해당 행에서 이 3개 컬럼 중 하나라도 True(즉, 1)이면 True 반환
        # .astype(int)를 통해 True는 1로, False는 0으로 변환
        df['CRE(R)'] = df[cre_source_cols].any(axis=1).astype(int)
        print("\n--- 'CRE(R)' 컬럼 생성 완료 (CIMP(R), CMEM(R), CETP(R) 기반) ---")
        print(df[['CIMP(R)', 'CMEM(R)', 'CETP(R)', 'CRE(R)']].head()) # 생성 결과 확인

        # '검사시행일자' 컬럼을 datetime 형식으로 변환
        df['검사시행일자'] = pd.to_datetime(df['검사시행일자'], errors='coerce')

        # 검사시행일자가 NaT인 경우는 제외
        df.dropna(subset=['검사시행일자'], inplace=True)

        # '검사시행일자'를 기준으로 '년월' 컬럼 생성 (월 단위)
        df['년월'] = df['검사시행일자'].dt.to_period('M')
        # '검사시행일자'를 기준으로 '년도' 컬럼 생성 (연도 단위)
        df['년도'] = df['검사시행일자'].dt.year

        # 각 감염병 유형별 First Isolation 데이터프레임을 저장할 딕셔너리
        first_isolation_dfs = {}

        # --- CRE First Isolation 데이터 처리 (환자별, 검체별, 년도별 기준) ---
        print("\n========== CRE First Isolation 데이터 처리 시작 ==========")
        # 이제 CRE First Isolation은 새로 생성된 'CRE(R)' 컬럼을 기준으로 합니다.
        cre_target_col = 'CRE(R)'
        df_cre_only = df[df[cre_target_col] == 1].copy()
        if df_cre_only.empty:
            print(f"경고: '{cre_target_col}' 컬럼 값이 1인 데이터가 없어 CRE First Isolation을 수행할 수 없습니다.")
            first_isolation_dfs['CRE'] = pd.DataFrame()
        else:
            print(f"'{cre_target_col}'이 1인 원본 데이터 수: {len(df_cre_only)} 행")
            # 환자번호, 검체명(주검체), 년도를 기준으로 그룹화하여 첫 번째 발생만 선택
            df_cre_first_isolation = df_cre_only.sort_values(by='검사시행일자').groupby(
                ['환자번호', '검체명(주검체)', '년도'], as_index=False
            ).first()
            first_isolation_dfs['CRE'] = df_cre_first_isolation
            print(f"CRE First Isolation 적용 후 데이터 수: {len(df_cre_first_isolation)} 행")
            print("CRE First Isolation 적용 후 데이터프레임의 상위 5행:")
            print(df_cre_first_isolation[['환자번호', '검체명(주검체)', '년도', '검사시행일자', cre_target_col]].head())

            # --- 연도별 CRE First Isolation 건수 ---
            print(f"\n--- 연도별 CRE First Isolation 건수 ---")
            annual_cre_first_isolation_counts = df_cre_first_isolation['년도'].value_counts().sort_index()
            print(annual_cre_first_isolation_counts)
            print(f"\n총 CRE First Isolation 건수: {len(df_cre_first_isolation)} 건")

            # --- 연도별 총 균주분리 건수 (원본 데이터 기준) ---
            print(f"\n--- 연도별 총 균주분리 건수 (원본 데이터 기준) ---")
            total_annual_isolates = df['년도'].value_counts().sort_index()
            print(total_annual_isolates)

            # --- CRE 건수 천균주분리 기준 연도별 계산 ---
            print(f"\n--- CRE 건수 천균주분리 기준 (연도별) ---")
            merged_counts_cre = pd.DataFrame({
                'CRE First Isolation': annual_cre_first_isolation_counts,
                'Total Isolates': total_annual_isolates
            }).fillna(0)

            merged_counts_cre['CRE per 1000 Isolates'] = (
                                                                 merged_counts_cre['CRE First Isolation'] /
                                                                 merged_counts_cre['Total Isolates']
                                                         ) * 1000
            print(merged_counts_cre)

        # --- VRSA (SVAN(R)) First Isolation 데이터 처리 (환자별, 검체별, 년도별 기준) ---
        print("\n========== VRSA (SVAN(R)) First Isolation 데이터 처리 시작 ==========")
        vrsa_target_col = 'SVAN(R)' # VRSA는 기존 컬럼 그대로 사용
        vrsa_required_cols = [vrsa_target_col]
        if not all(col in df.columns for col in vrsa_required_cols):
            print(f"오류: VRSA 분석을 위한 필수 컬럼 '{vrsa_required_cols[0]}'을(를) 찾을 수 없습니다. 엑셀 파일의 컬럼 이름을 확인해주세요.")
            first_isolation_dfs['VRSA'] = pd.DataFrame()
            print("VRSA 분석을 건너뜜니다.")
        else:
            df_vrsa_only = df[df[vrsa_target_col] == 1].copy()
            if df_vrsa_only.empty:
                print(f"경고: '{vrsa_target_col}' 컬럼 값이 1인 데이터가 없어 VRSA First Isolation을 수행할 수 없습니다.")
                first_isolation_dfs['VRSA'] = pd.DataFrame()
            else:
                print(f"'{vrsa_target_col}'이 1인 원본 데이터 수: {len(df_vrsa_only)} 행")
                # 환자번호, 검체명(주검체), 년도를 기준으로 그룹화하여 첫 번째 발생만 선택
                df_vrsa_first_isolation = df_vrsa_only.sort_values(by='검사시행일자').groupby(
                    ['환자번호', '검체명(주검체)', '년도'], as_index=False
                ).first()
                first_isolation_dfs['VRSA'] = df_vrsa_first_isolation
                print(f"VRSA First Isolation 적용 후 데이터 수: {len(df_vrsa_first_isolation)} 행")
                print("VRSA First Isolation 적용 후 데이터프레임의 상위 5행:")
                print(df_vrsa_first_isolation[['환자번호', '검체명(주검체)', '년도', '검사시행일자', vrsa_target_col]].head())

                # --- 연도별 VRSA (SVAN(R)) First Isolation 건수 ---
                print(f"\n--- 연도별 VRSA (SVAN(R)) First Isolation 건수 ---")
                annual_vrsa_first_isolation_counts = df_vrsa_first_isolation['년도'].value_counts().sort_index()
                print(annual_vrsa_first_isolation_counts)
                print(f"\n총 VRSA (SVAN(R)) First Isolation 건수: {len(df_vrsa_first_isolation)} 건")

                # --- VRSA 건수 천균주분리 기준 연도별 계산 ---
                print(f"\n--- VRSA 건수 천균주분리 기준 (연도별) ---")
                merged_counts_vrsa = pd.DataFrame({
                    'VRSA First Isolation': annual_vrsa_first_isolation_counts,
                    'Total Isolates': total_annual_isolates
                }).fillna(0)

                merged_counts_vrsa['VRSA per 1000 Isolates'] = (
                                                                       merged_counts_vrsa['VRSA First Isolation'] /
                                                                       merged_counts_vrsa['Total Isolates']
                                                               ) * 1000
                print(merged_counts_vrsa)

        # --- 모든 2급감염병의 연도별 First Isolation 건수 합계 (참고용) ---
        print("\n========== 연도별 2급감염병 건수 합계 (참고용) ==========")

        cre_counts_series_annual = first_isolation_dfs['CRE']['년도'].value_counts().sort_index() \
            if 'CRE' in first_isolation_dfs and not first_isolation_dfs['CRE'].empty else pd.Series(dtype=int)
        vrsa_counts_series_annual = first_isolation_dfs['VRSA']['년도'].value_counts().sort_index() \
            if 'VRSA' in first_isolation_dfs and not first_isolation_dfs['VRSA'].empty else pd.Series(dtype=int)

        combined_annual_counts = pd.DataFrame({
            'CRE': cre_counts_series_annual,
            'VRSA': vrsa_counts_series_annual
        }).fillna(0).astype(int)

        combined_annual_counts['2급감염병'] = combined_annual_counts[['CRE', 'VRSA']].sum(axis=1)
        combined_annual_counts = combined_annual_counts.sort_index()
        print("\n--- 연도별 2급감염병 건수 요약 ---")
        print(combined_annual_counts)

        # --- 최종 결과 엑셀 파일로 저장: 월별 First Isolation 건수 요약 ---
        output_file_name = '연도별_2급감염병_건수.xlsx'
        print(f"\n========== 월별 2급감염병 건수 요약 엑셀 파일 저장 시작 ==========")

        # CRE 월별 건수: 연도별 First Isolation 데이터에서 다시 월별로 집계
        cre_monthly_counts = first_isolation_dfs['CRE']['년월'].value_counts().sort_index() \
            if 'CRE' in first_isolation_dfs and not first_isolation_dfs['CRE'].empty else pd.Series(dtype=int)

        # VRSA 월별 건수: 연도별 First Isolation 데이터에서 다시 월별로 집계
        vrsa_monthly_counts = first_isolation_dfs['VRSA']['년월'].value_counts().sort_index() \
            if 'VRSA' in first_isolation_dfs and not first_isolation_dfs['VRSA'].empty else pd.Series(dtype=int)

        final_monthly_summary = pd.DataFrame({
            'CRE': cre_monthly_counts,
            'VRSA': vrsa_monthly_counts
        }).fillna(0).astype(int)

        final_monthly_summary = final_monthly_summary.reset_index().rename(columns={'index': '년월'})
        final_monthly_summary['2급감염병'] = final_monthly_summary['CRE'] + final_monthly_summary['VRSA']
        final_monthly_summary['년월'] = final_monthly_summary['년월'].astype(str)
        final_monthly_summary = final_monthly_summary.sort_values(by='년월').reset_index(drop=True)

        try:
            final_monthly_summary.to_excel(output_file_name, sheet_name='Monthly_2nd_Class_Infection_Counts',
                                           index=False)
            print(f"성공적으로 '{output_file_name}' 파일의 'Monthly_2nd_Class_Infection_Counts' 시트에 저장되었습니다.")
        except Exception as e:
            print(f"오류: 엑셀 파일 저장 중 오류 발생: {e}")

    except Exception as e:
        print(f"데이터 처리 중 오류 발생: {e}")

print(f"\n--- '{file_path}'에서 2급감염병 건수 세기 완료 ---")