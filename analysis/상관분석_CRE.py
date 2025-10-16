
# 라이브러리
import pandas as pd
import os
import warnings
import matplotlib.pyplot as plt
import seaborn as sns

# 한글 폰트 설정 (Windows 기준)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 경고 메시지 무시
warnings.filterwarnings('ignore')






# 경로
file_path = 'CRE_merged.xlsx'

try:
    # 1. 엑셀 파일 불러오기
    print("='데이터 불러오는 중...'\n")
    df = pd.read_excel(file_path)
    print("='데이터 불러오기 완료.'")
    print("='데이터 프레임의 상위 5행:'")
    print(df.head())
    print("\n")

    # 2. 상관분석에 필요한 컬럼만 선택
    # 'ds' 컬럼은 날짜/시간 데이터이므로 상관분석에서는 제외합니다.
    # 이미지 상의 컬럼 이름 'y', 'CRE_전국', 'CRE_충북'을 사용합니다.
    target_columns = ['CRE_내부', 'CRE_전국', 'CRE_충북', 'CRE_사망']

    # 선택된 컬럼이 데이터프레임에 존재하는지 확인
    for col in target_columns:
        if col not in df.columns:
            raise KeyError(f"지정된 컬럼 '{col}'이(가) 엑셀 파일에 존재하지 않습니다. 컬럼 이름을 확인해주세요.")

    correlation_data = df[target_columns]

    # 3. 상관관계 행렬 계산 (피어슨 상관계수)
    print("='상관관계 행렬 계산 중...'\n")
    correlation_matrix = correlation_data.corr()

    # 4. 상관관계 행렬 출력
    print("='='y', 'CRE_전국', 'CRE_충북' 컬럼 간의 상관관계 행렬='\n")
    print(correlation_matrix)
    print("\n")

    # 5. 상관관계 그래프 시각화
    # 히트맵 그리기
    print("='상관관계 히트맵 생성 중...'\n")
    plt.figure(figsize=(8, 6)) # 그래프 크기 설정
    sns.heatmap(
        correlation_matrix,
        annot=True,        # 각 셀에 상관계수 값 표시
        cmap='coolwarm',   # 색상 맵 설정 (양의 상관관계: 따뜻한 색, 음의 상관관계: 차가운 색)
        fmt=".2f",         # 숫자를 소수점 둘째 자리까지 표시
        linewidths=.5,     # 셀 사이의 구분선 너비 설정
        cbar_kws={'label': 'Correlation Coefficient'} # 컬러바 라벨
    )
    plt.title('Correlation Heatmap of Selected Columns', fontsize=16)
    plt.show()
    print("='히트맵 생성 완료.'\n")

    # 산점도 행렬 그리기 (Pair Plot)
    print("='산점도 행렬 생성 중...'\n")
    # KDE 플롯 (부드러운 밀도 곡선)
    sns.pairplot(correlation_data, diag_kind='kde')
    plt.suptitle('Pair Plot of Selected Columns (KDE)', y=1.02, fontsize=16) # 전체 제목
    plt.show()

    # 히스토그램
    sns.pairplot(correlation_data, diag_kind='hist')
    plt.suptitle('Pair Plot of Selected Columns (Histogram)', y=1.02, fontsize=16) # 전체 제목
    plt.show()
    print("='산점도 행렬 생성 완료.'\n")

    print("='분석 및 시각화 프로세스 완료.'")

except FileNotFoundError:
    print(f"\n오류: '{file_path}' 파일을 찾을 수 없습니다. 파일 경로를 다시 확인해주세요.")
except KeyError as e:
    print(f"\n오류: {e}")
    print("엑셀 파일 내의 컬럼 이름이 스크립트에 사용된 이름과 일치하는지 확인해주세요.")
except Exception as e:
    print(f"\n예상치 못한 오류가 발생했습니다: {e}")
    print("데이터 또는 환경 설정을 다시 확인해주세요.")
