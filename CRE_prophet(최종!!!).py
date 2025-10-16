# 라이브러리 임포트
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
import matplotlib.dates as mdates
import seaborn as sns
import logging
import warnings

from prophet.diagnostics import performance_metrics
from prophet.plot import plot_components

# 설정
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
logging.getLogger('prophet').setLevel(logging.WARNING)
warnings.filterwarnings('ignore')
plt.rcParams['font.family'] = 'Malgun Gothic'  # 맑은 고딕 (한글용)
plt.rcParams['axes.unicode_minus'] = False     # 음수 부호 깨짐 방지




# 1. 데이터 로드 및 전처리
df = pd.read_excel("CRE_FULL.xlsx")
df['ds'] = pd.to_datetime(df['년월'])
df = df.rename(columns={
    'CRE_내부': 'y',
    'CRE_전국': 'nationwide_cre',
    'CRE_충북': 'chungbuk_cre',
    'CRE_사망': 'cre_deaths'
})





# 2. 외부 변수 Prophet으로 개별 예측
external_vars = ['nationwide_cre', 'chungbuk_cre', 'cre_deaths']
future_external_preds = {}

for var in external_vars:
    ext_df = df[['ds', var]].copy().dropna()
    ext_df = ext_df.rename(columns={var: 'y'})

    model = Prophet()
    model.fit(ext_df)

    # 예측은 2024년 3월까지 (2023년 12월 기준 future 3개월)
    future = model.make_future_dataframe(periods=3, freq='M')
    forecast = model.predict(future)

    future_external_preds[var] = forecast[['ds', 'yhat']].rename(columns={'yhat': f'{var}_예측'})






# 3. 외부 변수 예측값 병합
external_merged = future_external_preds[external_vars[0]]
for var in external_vars[1:]:
    external_merged = pd.merge(external_merged, future_external_preds[var], on='ds', how='outer')

# 내부 데이터와 병합
internal_df = df[['ds', 'y']]
full_model_df = pd.merge(internal_df, external_merged, on='ds', how='left')






# 4. 내부 Prophet 모델 학습
train_df = full_model_df.dropna(subset=['y'])

model = Prophet()
for var in external_vars:
    model.add_regressor(f'{var}_예측')

model.fit(train_df[['ds', 'y'] + [f'{var}_예측' for var in external_vars]])

# 전체 예측 (2021~2024.03)
forecast = model.predict(full_model_df[['ds'] + [f'{var}_예측' for var in external_vars]])







# 5. 회귀변수 영향력 확인
# 회귀계수 시각화 (외부 변수 회귀 효과 확인)
model.plot_components(forecast)
plt.show()

# 실제 prophet에 추가한 변수 이름 리스트
regressors = [f'{var}_예측' for var in external_vars]

# model.extra_regressors에는 실제 사용한 외부 변수 이름이 저장돼 있음
true_regressors = list(model.extra_regressors.keys())

# 회귀계수 추출 (순서 일치 확인 필요)
coefs = model.params['beta'].mean(axis=0)

# 회귀계수 개수와 변수 이름 개수 일치 여부 확인
print(f"회귀계수 개수: {len(coefs)}")
print(f"실제 외부변수 개수: {len(true_regressors)}")

# 매칭 데이터프레임 생성
coef_df = pd.DataFrame({
    '변수': true_regressors,
    '회귀계수': coefs[:len(true_regressors)]
})

# 출력 확인
print(coef_df)

# 영향력 높은 순으로 정렬
coef_df = coef_df.sort_values(by='회귀계수', key=abs, ascending=False)
print(coef_df)

# 변수 중요도 시각화
plt.figure(figsize=(10, 5))
sns.barplot(data=coef_df, x='회귀계수', y='변수', palette='coolwarm')
plt.title('📌 Prophet 외부 변수 영향력 (회귀계수)')
plt.xlabel('회귀계수')
plt.ylabel('변수')
plt.tight_layout()
plt.show()






# 6. 성능지표 계산
forecast_df = pd.merge(full_model_df[['ds', 'y']], forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']], on='ds',
                       how='left')
forecast_df['year'] = forecast_df['ds'].dt.year

# 연도별 MAE, RMSE, MAPE
results = []
for yr in [2021, 2022, 2023]:
    subset = forecast_df[forecast_df['year'] == yr].dropna()
    mae = mean_absolute_error(subset['y'], subset['yhat'])
    rmse = np.sqrt(mean_squared_error(subset['y'], subset['yhat']))
    mape = mean_absolute_percentage_error(subset['y'], subset['yhat']) * 100
    results.append({'Year': yr, 'MAE': mae, 'RMSE': rmse, 'MAPE': mape})

results_df = pd.DataFrame(results)

# 2022 & 2023 평균
avg_result = results_df[results_df['Year'].isin([2022, 2023])].mean(numeric_only=True)

# 결과 출력
print("📊 연도별 롤링 예측 평균 성능지표:")
print(results_df.round(3).to_string(index=False))
print("\n📌 2022년과 2023년 평균 성능지표:")
print(f"MAE:  {avg_result['MAE']:.3f}")
print(f"RMSE: {avg_result['RMSE']:.3f}")
print(f"MAPE: {avg_result['MAPE']:.3f}")

# 막대 그래프 시각화
plt.figure(figsize=(10, 5))
bar_width = 0.25
x = np.arange(len(results_df['Year']))

plt.bar(x - bar_width, results_df['MAE'], width=bar_width, label='MAE')
plt.bar(x, results_df['RMSE'], width=bar_width, label='RMSE')
plt.bar(x + bar_width, results_df['MAPE'], width=bar_width, label='MAPE')

plt.xticks(x, results_df['Year'].astype(str))
plt.title('연도별 Prophet 롤링 예측 성능 비교 (MAE / RMSE / MAPE)')
plt.ylabel('오차 지표 값')
plt.xlabel('연도')
plt.legend()
plt.grid(axis='y')
plt.tight_layout()
plt.show()

# 연도별 꺾은선 그래프
plt.figure(figsize=(10, 6))
plt.plot(results_df['Year'], results_df['MAE'], marker='o', label='MAE')
plt.plot(results_df['Year'], results_df['RMSE'], marker='o', label='RMSE')
plt.plot(results_df['Year'], results_df['MAPE'], marker='o', label='MAPE')

plt.title('연도별 Prophet 롤링 예측 성능 추이 (지표별 꺾은선)', fontsize=14)
plt.xlabel('연도')
plt.ylabel('오차 지표 값')
plt.xticks(results_df['Year'])
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()







# 7. 예측 시각화 (2021.01 ~ 2024.03 구간만 필터링)
plot_df = forecast_df[(forecast_df['ds'] >= '2021-01-01') & (forecast_df['ds'] <= '2024-03-31')]
plt.figure(figsize=(12, 5))
sns.set(style="whitegrid")

# 신뢰구간
plt.fill_between(plot_df['ds'], plot_df['yhat_lower'], plot_df['yhat_upper'],
                 color='red', alpha=0.2, label='신뢰구간 (95%)')

# 실제값, 예측값
plt.plot(plot_df['ds'], plot_df['y'], 'o-', label='실제값', color='blue')
plt.plot(plot_df['ds'], plot_df['yhat'], 'o--', label='예측값', color='red')

# 포맷
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

plt.title('CRE 내부 Prophet 예측 결과 (2021~2023 + 미래 3개월)', fontsize=13)
plt.xlabel('날짜')
plt.ylabel('CRE 발생건수')
plt.xticks(rotation=45)
plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.legend()
plt.tight_layout()
plt.show()




# 8. 경보 로직 (y > yhat_upper 기준)
forecast_df['경보'] = False
alarm_msgs = []

for i in range(len(forecast_df)):
    current_y = forecast_df.loc[i, 'y']
    current_upper = forecast_df.loc[i, 'yhat_upper']
    if pd.notna(current_y) and pd.notna(current_upper) and current_y > current_upper:
        forecast_df.at[i, '경보'] = True
        msg = f"📢 경보 발생: {forecast_df.loc[i, 'ds'].strftime('%Y-%m')} - 실제값 {current_y:.1f} > 예측상한 {current_upper:.1f}"
        print(msg)
        alarm_msgs.append(msg)


# 엑셀 저장 (경보 포함)
save_cols = ['ds', 'y', 'yhat', 'yhat_lower', 'yhat_upper', '경보']
forecast_df[save_cols].to_excel("CRE_경보결과.xlsx", index=False)

# 시각화: 2023-01 ~ 2024-01
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

plot_df = forecast_df[(forecast_df['ds'] >= '2023-01-01') & (forecast_df['ds'] <= '2024-01-31')]

plt.figure(figsize=(12, 6))

# 신뢰구간
plt.fill_between(plot_df['ds'], plot_df['yhat_lower'], plot_df['yhat_upper'],
                 color='red', alpha=0.2, label='신뢰구간 (95%)')

# 예측값 (전체 구간)
plt.plot(plot_df['ds'], plot_df['yhat'], 'o--', color='red', label='예측값')

# 실제값 (2023-09까지 표시)
cutoff_date = pd.to_datetime('2023-09-30')
observed = plot_df[(plot_df['ds'] <= cutoff_date) & (plot_df['y'].notna())]
plt.plot(observed['ds'], observed['y'], 'o-', color='blue', label='실제 CRE 건수')

# 이상치 (경보) 마커 표시 (예측구간에서만)
alerts = plot_df[(plot_df['ds'] > cutoff_date) & (plot_df['경보']) & (plot_df['y'].notna())]
plt.plot(alerts['ds'], alerts['y'], 'p', color='gold', markersize=10,
         markeredgecolor='black', label='이상치 (경보)')

# 예측 시작선
plt.axvline(pd.to_datetime('2023-10-01'), color='gray', linestyle='--', label='예측 시작 (2023-10)')

# 포맷
plt.title('CRE 이상치 탐지 (2023-01 ~ 2024-01)', fontsize=14)
plt.xlabel('날짜')
plt.ylabel('CRE 건수')
plt.xticks(rotation=45)
plt.legend()
plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.tight_layout()
plt.show()







# 9. 구성요소 추출 및 저장
# Prophet 예측 수행 (기존 단계예측 모델 기준)
forecast = model.predict(full_model_df[['ds'] + [f'{var}_예측' for var in external_vars]])

# 추출 대상 기본 컬럼
cols_to_export = ['ds', 'yhat']

# forecast에 있는 컬럼만 추가
for comp in ['trend', 'seasonal', 'yearly', 'monthly', 'weekly']:
    if comp in forecast.columns:
        cols_to_export.append(comp)

# 안전하게 추출
component_df = forecast[cols_to_export]

# 엑셀 저장
component_df.to_excel("CRE_구성요소_결과.xlsx", index=False)