# 라이브러리 임포트
import pandas as pd
import matplotlib.pyplot as plt

# 설정
plt.rcParams['font.family'] = 'Malgun Gothic'  # 맑은 고딕 (한글용)
plt.rcParams['axes.unicode_minus'] = False     # 음수 부호 깨짐 방지

# 1) 데이터 로드
df = pd.read_excel("CRE_FULL.xlsx")

# 2) 날짜 컬럼 생성/정리 (년월 -> datetime)
# - 엑셀에 '년월' 컬럼이 있고, 예: 2021-01 / 2021.01 / 202101 형태일 수 있어서 문자열로 안전하게 처리
df["ds"] = pd.to_datetime(df["년월"].astype(str), errors="coerce")

# 3) y 컬럼 준비
df["y"] = df["CRE_내부"]

# 4) 정렬 + 결측 제거
df = df.sort_values("ds")
df = df.dropna(subset=["ds", "y"])

# 5) 시계열 꺾은선 그래프
plt.figure(figsize=(12, 5))
plt.plot(df["ds"], df["y"], color="blue", marker="o", linewidth=2)

plt.title("CRE_내부 감염병 발생 추이")
plt.xlabel("날짜")
plt.ylabel("CRE_발생건수")

plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
