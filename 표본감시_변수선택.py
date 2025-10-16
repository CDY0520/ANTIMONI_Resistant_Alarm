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

# 1. 데이터 로딩
df = pd.read_excel("표본감시_FULL.xlsx")
df['ds'] = pd.to_datetime(df['년월'])
df = df.rename(columns={'표본감시': 'y'})

# 회귀변수 리스트
reg_vars = [
    'MRSA_혈액', 'VRE_혈액', 'MRPA_혈액', 'MRAB_혈액',
    'MRSA_그외', 'VRE_그외', 'MRPA_그외', 'MRAB_그외'
]

# 2. 실험 조합 정의
variable_sets = {
    'MRSA_혈액': ['MRSA_혈액'],
    'VRE_혈액': ['VRE_혈액'],
    'MRAB_혈액': ['MRAB_혈액'],
    '혈액_Top2': ['MRSA_혈액', 'MRAB_혈액'],
    '혈액+그외': ['MRSA_혈액', 'VRE_혈액', 'MRSA_그외'],
    '그외_Top2': ['MRSA_그외', 'MRAB_그외'],
    '전부사용': reg_vars
}

# 3. 성능 결과 저장용 리스트
results = []

# 4. 변수 조합별 Prophet 실험
for name, regressors in variable_sets.items():
    train_df = df[(df['ds'] < '2023-01-01') & df['y'].notna()]
    valid_df = df[(df['ds'] >= '2023-01-01') & (df['ds'] <= '2023-12-31')]

    model = Prophet()
    for reg in regressors:
        model.add_regressor(reg)
    model.fit(train_df[['ds', 'y'] + regressors])

    future = valid_df[['ds'] + regressors]
    forecast = model.predict(future)

    y_true = valid_df['y'].values
    y_pred = forecast['yhat'].values

    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    results.append({
        '조합': name,
        'MAE': mae,
        'RMSE': rmse,
        'MAPE': mape
    })

# 5. 결과 정리 및 출력
result_df = pd.DataFrame(results).sort_values(by='RMSE')
print("📊 변수 조합별 Prophet 예측 성능 비교 (2023년 기준):")
print(result_df)

# 6. 시각화
plt.figure(figsize=(10, 6))
plt.plot(result_df['조합'], result_df['MAE'], marker='o', label='MAE')
plt.plot(result_df['조합'], result_df['RMSE'], marker='o', label='RMSE')
plt.plot(result_df['조합'], result_df['MAPE'], marker='o', label='MAPE')
plt.title("📈 표본감시 회귀변수 조합에 따른 예측 성능 (2023년)", fontsize=14)
plt.ylabel("오차 지표")
plt.xticks(rotation=45)
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
