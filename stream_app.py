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

# 설정
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
logging.getLogger('prophet').setLevel(logging.WARNING)
warnings.filterwarnings('ignore')

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = font_prop.get_name()

font_path = './fonts/NotoSansKR-VariableFont_wght.ttf'
fontprop = fm.FontProperties(fname=font_path)





# 1. Streamlit 설정
st.set_page_config(layout="wide")
st.title("📈 이상치 탐지 모니터링")
st.write("예측 결과 및 이상치 경보를 확인하세요.")




# 2. 드롭박스 가로 2개 배치
col1, col2 = st.columns(2)
with col1:
    hospital_choice = st.selectbox("🏥 병원 감염 선택", ["선택", "CRE(충북대병원)", "표본감시(충북대병원)"], index=0)
with col2:
    community_choice = st.selectbox("🌎 지역사회 감염 선택", ["선택", "CRE(전국)", "CRE(충북)", "표본감시(전국)", "표본감시(충북)"], index=0)




# 3. 파일 맵 정의
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




# 4. 공통 출력 리스트
alarm_records = []





# 5. 시각화 함수
def plot_graph(df, title_text, y_label, current_date):
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.patches as mpatches

    past_mask = df['ds'] < current_date
    current_mask = df['ds'] == current_date

    fig, ax = plt.subplots(figsize=(6, 2.2))  # 👈 작고 넓게
    fig.patch.set_facecolor('#FFF7F0')  # 전체 배경색

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

    # 이상치
    outlier_label_added = False
    if '경보' in df.columns:
        outlier_rows = df[df['경보'].fillna(False) == True]
        for _, row in outlier_rows.iterrows():
            edge_color = 'black' if row['ds'] == current_date else 'gray'
            ax.plot(row['ds'], row['y'], marker='*', color='#FFC107', markersize=6,
                    markeredgecolor=edge_color,
                    label='이상치' if not outlier_label_added else None)
            outlier_label_added = True

    # 예측 시작선
    ax.axvline(current_date, color='gray', linestyle='--', linewidth=0.8, label='예측 시작')

    # 축/글자 설정
    ax.set_title(title_text, fontsize=6, color='#2B2D42')
    ax.set_xlabel("날짜", fontsize=5, color='#2B2D42')
    ax.set_ylabel(y_label, fontsize=5, color='#2B2D42')
    ax.tick_params(axis='both', labelsize=4, colors='#2B2D42')
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    ax.grid(True, color='#CCCCCC', linestyle='--', linewidth=0.4)

    # 범례 구성
    handles, labels = ax.get_legend_handles_labels()
    label_handle_map = dict(zip(labels, handles))

    # '이상치' 더미 추가 (없을 경우 대비)
    if '이상치' not in label_handle_map:
        dummy_star = mpatches.Patch(facecolor='gold', edgecolor='black', label='이상치')
        label_handle_map['이상치'] = dummy_star

    # 원하는 순서대로 범례 정렬
    order = ['신뢰구간 (95%)', f'실제 {y_label}', 'One-step 예측', '이상치', '예측 시작']
    ordered_handles = [label_handle_map[lbl] for lbl in order if lbl in label_handle_map]
    ordered_labels = [lbl for lbl in order if lbl in label_handle_map]

    ax.legend(ordered_handles, ordered_labels,
              fontsize=4, markerscale=0.7, loc='upper left', frameon=False)

    st.pyplot(fig)








# 6. 경보 내역 렌더링 함수
def render_alarms(alarm_records, current_date):
    st.markdown("### 🛎️ 경보 내역", unsafe_allow_html=True)

    for name, raw_df in alarm_records:
        st.markdown(f"#### 📌 {name}")

        if '경보' not in raw_df.columns:
            st.warning(f"⚠️ [{name}]에는 '경보' 컬럼이 없어 경보 내역을 표시할 수 없습니다.")
            continue

        alarm_df = raw_df[raw_df['경보'].fillna(False) == True].copy()
        current_alarm = alarm_df[alarm_df['ds'] == current_date]
        past_alarms = alarm_df[alarm_df['ds'] < current_date].copy()

        # ✅ 현재 경보가 있는 경우
        if not current_alarm.empty:
            row = current_alarm.iloc[0]

            st.markdown(f"""
            <div style='background-color:#fff4e5; padding:10px 14px; border-radius:6px;
                        border-left: 5px solid #ff8800; font-size: 14px; margin-bottom:8px;'>

              <div style='color:red; font-weight:bold; margin-bottom:6px'>
                📌 현재 경보 발생 ({row['ds'].strftime('%Y-%m')})
              </div>

              <div style='color:black; margin-bottom:4px'> 
                ▶ 실제값 <b>{row['y']:.0f}</b>이(가) 예측상한 <b>{row['yhat_upper']:.2f}</b>을(를) 초과하였습니다.
              </div>
              {"".join([f"<div style='color:black;'>▶ {line.strip()}</div>"
                        for line in str(row['경보해석']).splitlines() if line.strip()])}

            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(
                f"<span style='font-size:13px;color:gray'>📭 현재({current_date.strftime('%Y-%m')})에는 경보가 없습니다.</span>",
                unsafe_allow_html=True)

        # ✅ 과거 경보 테이블
        if not past_alarms.empty:
            st.markdown("<div style='margin-top:10px; font-size:13px'><b>📜 과거 경보 내역</b></div>", unsafe_allow_html=True)
            display_df = past_alarms[['ds', 'y', 'yhat_upper']].copy()
            display_df.columns = ['날짜', '실제값', '예측상한']
            display_df['날짜'] = display_df['날짜'].dt.strftime('%Y-%m')
            display_df['실제값'] = display_df['실제값'].apply(lambda x: f"{int(x)}")
            display_df['예측상한'] = display_df['예측상한'].apply(lambda x: f"{x:.2f}")
            st.table(display_df.reset_index(drop=True))
        else:
            st.markdown("<span style='font-size:13px;color:gray'>과거 경보 내역 없음</span>", unsafe_allow_html=True)






# 7. 현재 시점 및 좌우 분할 설정
# 현재 시점
current_date = pd.to_datetime('2023-08-01')

# 레이아웃 좌우 분할
left_col, right_col = st.columns(2)

# ✅ 병원 감염 (왼쪽 영역)
with left_col:
    if hospital_choice != "선택":
        file, title, ylabel = hospital_file_map[hospital_choice]
        if os.path.exists(file):
            raw_df = pd.read_excel(file)
            raw_df['ds'] = pd.to_datetime(raw_df['ds'])
            df = raw_df[(raw_df['ds'] >= '2023-01-01') & (raw_df['ds'] <= '2023-12-31')].copy()
            st.subheader(f"🏥 {hospital_choice}")
            plot_graph(df, title, ylabel, current_date)
            render_alarms([(hospital_choice, raw_df)], current_date)
        else:
            st.warning(f"⚠️ [{hospital_choice}] 데이터는 아직 준비되지 않았습니다.")

# ✅ 지역사회 감염 (오른쪽 영역)
with right_col:
    if community_choice != "선택":
        if community_choice in community_file_map:
            file, title, ylabel = community_file_map[community_choice]
            if os.path.exists(file):
                raw_df = pd.read_excel(file)
                raw_df['ds'] = pd.to_datetime(raw_df['ds'])
                df = raw_df[(raw_df['ds'] >= '2023-01-01') & (raw_df['ds'] <= '2023-12-31')].copy()
                st.subheader(f"🌎 {community_choice}")
                plot_graph(df, title, ylabel, current_date)
                render_alarms([(community_choice, raw_df)], current_date)
            else:
                st.warning(f"⚠️ [{community_choice}] 데이터는 아직 준비되지 않았습니다.")
        else:
            st.warning(f"⚠️ [{community_choice}] 데이터는 아직 준비되지 않았습니다.")
