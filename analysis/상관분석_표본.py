# 라이브러리
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 경고 무시
import warnings
warnings.filterwarnings('ignore')




# 엑셀 파일 경로 설정 (★★★ 반드시 본인의 파일 경로에 맞게 수정해주세요 ★★★)
file_path = '표본감시_merged.xlsx'

try:
    # 1. 엑셀 파일 불러오기
    print("='데이터 불러오는 중...'\n")
    df = pd.read_excel(file_path)
    print("='데이터 불러오기 완료.'")
    print("='데이터 프레임의 상위 5행:'")
    print(df.head())
    print("\n")

    # 2. '년월' 컬럼을 제외한 나머지 컬럼 선택
    # df.columns에서 '년월'을 제외한 리스트를 만듭니다.
    columns_for_correlation = [col for col in df.columns if col != '년월']

    if not columns_for_correlation:
        raise ValueError("='상관분석을 수행할 컬럼이 없습니다. '년월'을 제외한 다른 컬럼이 있는지 확인해주세요.'")

    correlation_data = df[columns_for_correlation]

    # 3. 상관관계 행렬 계산 (피어슨 상관계수)
    print("='상관관계 행렬 계산 중...'\n")
    correlation_matrix = correlation_data.corr()

    # 4. 상관관계 행렬 출력
    print("='='년월'을 제외한 컬럼 간의 상관관계 행렬='\n")
    print(correlation_matrix)
    print("\n")

    # 5. 상관관계 그래프 시각화

    # 5-1. 상관관계 히트맵 그리기
    print("='상관관계 히트맵 생성 중...'\n")
    plt.figure(figsize=(10, 8)) # 그래프 크기 설정 (컬럼 수에 따라 조절)
    sns.heatmap(
        correlation_matrix,
        annot=True,        # 각 셀에 상관계수 값 표시
        cmap='coolwarm',   # 색상 맵 설정 (양의 상관관계: 따뜻한 색, 음의 상관관계: 차가운 색)
        fmt=".2f",         # 숫자를 소수점 둘째 자리까지 표시
        linewidths=.5,     # 셀 사이의 구분선 너비 설정
        cbar_kws={'label': 'Correlation Coefficient'} # 컬러바 라벨
    )
    plt.title('Correlation Heatmap of Variables (Excluding 년월)', fontsize=16)
    plt.show()
    print("='히트맵 생성 완료.'\n")

    # 5-2. 산점도 행렬 그리기 (Pair Plot)
    print("='산점도 행렬 생성 중...'\n")
    # KDE 플롯 (부드러운 밀도 곡선)
    # pairplot은 데이터가 많을수록 시간이 오래 걸릴 수 있습니다.
    sns.pairplot(correlation_data, diag_kind='kde')
    plt.suptitle('Pair Plot of Variables (Excluding 년월, KDE)', y=1.02, fontsize=16) # 전체 제목
    plt.show()

    # 히스토그램
    sns.pairplot(correlation_data, diag_kind='hist')
    plt.suptitle('Pair Plot of Variables (Excluding 년월, Histogram)', y=1.02, fontsize=16) # 전체 제목
    plt.show()
    print("='산점도 행렬 생성 완료.'\n")

    print("='분석 및 시각화 프로세스 완료.'")

except FileNotFoundError:
    print(f"\n오류: '{file_path}' 파일을 찾을 수 없습니다. 파일 경로를 다시 확인해주세요.")
except KeyError as e:
    print(f"\n오류: {e}")
    print("엑셀 파일 내의 컬럼 이름이 스크립트에 사용된 이름과 일치하는지 확인해주세요.")
except ValueError as e:
    print(f"\n오류: {e}")
except Exception as e:
    print(f"\n예상치 못한 오류가 발생했습니다: {e}")
    print("데이터 또는 환경 설정을 다시 확인해주세요.")
