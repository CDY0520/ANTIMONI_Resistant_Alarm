# 1. 라이브러리
import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import logging
import warnings

# 설정
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
logging.getLogger('prophet').setLevel(logging.WARNING)
warnings.filterwarnings('ignore')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 2. 데이터 로딩 및 전처리
df = pd.read_excel("CRE_FULL.xlsx")
df['ds'] = pd.to_datetime(df['년월'])
df = df.rename(columns={
    'CRE_내부': 'y',
    'CRE_전국': 'nationwide_cre',
    'CRE_충북': 'chungbuk_cre',
    'CRE_사망': 'cre_deaths'
})

# 3. 실험할 외부 변수 조합 정의
variable_sets = {
    "전국만": ['nationwide_cre'],
    "충북만": ['chungbuk_cre'],
    "사망만": ['cre_deaths'],
    "전국+충북": ['nationwide_cre', 'chungbuk_cre'],
    "전국+사망": ['nationwide_cre', 'cre_deaths'],
    "충북+사망": ['chungbuk_cre', 'cre_deaths'],
    "전부사용": ['nationwide_cre', 'chungbuk_cre', 'cre_deaths']
}

# 4. 성능 저장용 딕셔너리
results = []

# 5. 변수 조합별 Prophet 학습 및 예측
for name, regressors in variable_sets.items():
    # 데이터 분할
    train_df = df[(df['ds'] < '2023-01-01') & df['y'].notna()]
    valid_df = df[(df['ds'] >= '2023-01-01') & (df['ds'] <= '2023-12-31')]

    # 모델 학습
    model = Prophet(
        changepoint_prior_scale=0.01,
        seasonality_prior_scale=1.0
    )
    for reg in regressors:
        model.add_regressor(reg)
    model.fit(train_df[['ds', 'y'] + regressors])

    # 예측
    future = valid_df[['ds'] + regressors]
    forecast = model.predict(future)

    # 평가
    y_true = valid_df['y'].values
    y_pred = forecast['yhat'].values

    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    # 결과 저장
    results.append({
        '조합': name,
        'MAE': mae,
        'RMSE': rmse,
        'MAPE': mape
    })

# 6. 성능 결과 출력
result_df = pd.DataFrame(results)
print("📊 변수 조합별 성능 비교 (2023년 기준):")
print(result_df.sort_values(by='RMSE'))

# 7. 시각화
plt.figure(figsize=(10, 6))
plt.plot(result_df['조합'], result_df['MAE'], marker='o', label='MAE')
plt.plot(result_df['조합'], result_df['RMSE'], marker='o', label='RMSE')
plt.plot(result_df['조합'], result_df['MAPE'], marker='o', label='MAPE')
plt.title("외부 변수 조합에 따른 예측 성능 (2023년 기준)", fontsize=14)
plt.ylabel("오차 지표 값")
plt.legend()
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()
plt.show()
