# 라이브러리 임포트
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.dates as mdates
from datetime import datetime
import os
import logging
import warnings

# 경고 제거
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
logging.getLogger('prophet').setLevel(logging.WARNING)
warnings.filterwarnings('ignore')

# 폰트 설정
font_path = os.path.join("fonts", "NotoSansKR-VariableFont_wght.ttf")
if not os.path.exists(font_path):
    st.error(f"❌ 폰트 파일 경로 오류: {font_path} 에 파일이 없습니다.")
else:
    fontprop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = fontprop.get_name()
    plt.rcParams['axes.unicode_minus'] = False

# Streamlit UI 시작
st.set_page_config(layout="wide")
st.title("📈 이상치 탐지 모니터링")
st.write("예측 결과 및 이상치 경보를 확인하세요.")

# 드롭다운 메뉴
col1, col2 = st.columns(2)
with col1:
    hospital_choice = st.selectbox("🏥 병원 감염 선택", ["선택", "CRE(충북대병원)", "표본감시(충북대병원)"], index=0)
with col2:
    community_choice = st.selectbox("🌎 지역사회 감염 선택", ["선택", "CRE(전국)", "CRE(충북)", "표본감시(전국)", "표본감시(충북)"], index=0)

# 파일 매핑
hospital_file_map = {
    "CRE(충북대병원)": ("CRE(충북대)_경보결과.xlsx", "CRE(충북대병원) 이상치 탐지 (One-step 예측 기반)", "CRE 발생 건수"),
    "표본감시(충북대병원)": ("표본감시(충북대)_경보결과.xlsx", "표본감시(충북대병원) 이상치 탐지 (One-step 예측 기반)", "표본감시 발생 건수")
}

community_file_map = {
    "CRE(전국)": ("CRE(전국)_경보결과.xlsx", "CRE(전국) 이상치 탐지 (One-step 예측 기반)", "CRE 발생 건수"),
    "CRE(충북)": ("CRE(충북)_경보결과.xlsx", "CRE(충북) 이상치 탐지 (One-step 예측 기반)", "CRE 발생 건수"),
    "표본감시(전국)": ("표본감시(전국)_경보결과.xlsx", "표본감시(전국) 이상치 탐지 (One-step 예측 기반)", "표본감시 발생 건수"),
    "표본감시(충북)": ("표본감시(충북)_경보결과.xlsx", "표본감시(충북) 이상치 탐지 (One-step 예측 기반)", "표본감시 발생 건수")
}

# 시각화 함수
def plot_graph(df, title_text, y_label, current_date):
    import matplotlib.patches as mpatches

    past_mask = df['ds'] < current_date
    current_mask = df['ds'] == current_date

    fig, ax = plt.subplots(figsize=(6, 2.3))
    fig.patch.set_facecolor('#FFF7F0')

    # 신뢰구간
    ax.fill_between(df['ds'], df['yhat_lower'], df['yhat_upper'],
                    where=~df['yhat_lower'].isna(),
                    color='red', alpha=0.2, label='신뢰구간 (95%)')

    # 실제값
    ax.plot(df.loc[past_mask | current_mask, 'ds'],
            df.loc[past_mask | current_mask, 'y'],
            marker='o', color='royalblue', linestyle='-',
            markersize=2.5, linewidth=0.8, label=f'실제 {y_label}')

    # 예측값
    ax.plot(df['ds'], df['yhat'],
            marker='o', linestyle='--', color='red',
            markersize=2.5, linewidth=0.8, label='One-step 예측')

    # ✅ 이상치 처리
    outlier_label_added = False
    if '경보' in df.columns:
        df['경보'] = df['경보'].fillna(False)
        outlier_rows = df[df['경보']]
        for _, row in outlier_rows.iterrows():
            edge_color = 'black' if row['ds'] == current_date else 'gray'
            ax.plot(row['ds'], row['y'], marker='*', color='#FFC107', markersize=6,
                    markeredgecolor=edge_color,
                    label='이상치' if not outlier_label_added else None)
            outlier_label_added = True

    # 예측 시작선
    ax.axvline(current_date, color='gray', linestyle='--', linewidth=0.8, label='예측 시작')

    # 축, 폰트, 스타일
    ax.set_title(title_text, fontsize=7, fontproperties=fontprop)
    ax.set_xlabel("날짜", fontsize=6, fontproperties=fontprop)
    ax.set_ylabel(y_label, fontsize=6, fontproperties=fontprop)
    ax.tick_params(axis='both', labelsize=5, colors='#2B2D42')
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    ax.grid(True, linestyle='--', linewidth=0.4, color='#CCCCCC')

    # 범례 구성
    handles, labels = ax.get_legend_handles_labels()
    label_handle_map = dict(zip(labels, handles))
    order = ['신뢰구간 (95%)', f'실제 {y_label}', 'One-step 예측', '이상치', '예측 시작']
    ordered_handles = [label_handle_map[lbl] for lbl in order if lbl in label_handle_map]
    ordered_labels = [lbl for lbl in order if lbl in label_handle_map]

    ax.legend(ordered_handles, ordered_labels,
              fontsize=5, markerscale=0.7, loc='upper left', frameon=False, prop=fontprop)

    st.pyplot(fig)


# 경보 출력
def render_alarms(alarm_records, current_date):
    st.markdown("### 🛎️ 경보 내역")

    for name, raw_df in alarm_records:
        st.markdown(f"#### 📌 {name}")
        if '경보' not in raw_df.columns:
            st.warning("⚠️ '경보' 컬럼 없음")
            continue
        

        alarm_df = raw_df[raw_df['경보'].fillna(False)]
        current_alarm = alarm_df[alarm_df['ds'] == current_date]
        past_alarms = alarm_df[alarm_df['ds'] < current_date]

        if not current_alarm.empty:
            row = current_alarm.iloc[0]
            st.markdown(f"""
            <div style='background-color:#fff4e5; padding:10px 14px; border-radius:6px;
                        border-left: 5px solid #ff8800; font-size: 14px; margin-bottom:8px;'>

              <div style='color:red; font-weight:bold; margin-bottom:6px'>
                📌 현재 경보 발생 ({row['ds'].strftime('%Y-%m')})
              </div>

              <div style='color:black; margin-bottom:4px'> 
                ▶ 실제값 <b>{row['y']:.0f}</b>이(가) 예측상한 <b>{row['yhat_upper']:.2f}</b> 초과
              </div>
              {"".join([f"<div style='color:black;'>▶ {line.strip()}</div>"
                        for line in str(row['경보해석']).splitlines() if line.strip()])}

            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='font-size:13px;color:gray'>📭 현재({current_date.strftime('%Y-%m')})에는 경보가 없습니다.</span>",
                        unsafe_allow_html=True)

        if not past_alarms.empty:
            st.markdown("📜 과거 경보 내역")
            display_df = past_alarms[['ds', 'y', 'yhat_upper']].copy()
            display_df.columns = ['날짜', '실제값', '예측상한']
            display_df['날짜'] = display_df['날짜'].dt.strftime('%Y-%m')
            display_df['실제값'] = display_df['실제값'].astype(int)
            display_df['예측상한'] = display_df['예측상한'].round(2)
            st.table(display_df.reset_index(drop=True))
        else:
            st.markdown("과거 경보 내역 없음")

# 현재 날짜 설정
current_date = pd.to_datetime('2023-08-01')
left_col, right_col = st.columns(2)

# 병원 감염 (왼쪽)
with left_col:
    if hospital_choice != "선택":
        file, title, ylabel = hospital_file_map[hospital_choice]
        if os.path.exists(file):
            raw_df = pd.read_excel(file)
            raw_df['ds'] = pd.to_datetime(raw_df['ds'])
            df = raw_df[(raw_df['ds'] >= '2023-01-01') & (raw_df['ds'] <= '2023-12-31')].copy()
            st.subheader(f" {hospital_choice}")
            plot_graph(df, title, ylabel, current_date)
            render_alarms([(hospital_choice, raw_df)], current_date)
        else:
            st.warning(f"⚠️ [{hospital_choice}] 데이터 파일이 없습니다.")

# 지역사회 감염 (오른쪽)
with right_col:
    if community_choice != "선택":
        file, title, ylabel = community_file_map.get(community_choice, (None, None, None))
        if file and os.path.exists(file):
            raw_df = pd.read_excel(file)
            raw_df['ds'] = pd.to_datetime(raw_df['ds'])
            df = raw_df[(raw_df['ds'] >= '2023-01-01') & (raw_df['ds'] <= '2023-12-31')].copy()
            st.subheader(f" {community_choice}")
            plot_graph(df, title, ylabel, current_date)
            render_alarms([(community_choice, raw_df)], current_date)
        else:
            st.warning(f"⚠️ [{community_choice}] 데이터 파일이 없습니다.")
