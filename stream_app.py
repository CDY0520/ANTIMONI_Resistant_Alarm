# 0. 라이브러리 임포트 및 설정
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.dates as mdates
from datetime import datetime
import os
import plotly.graph_objects as go
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

# 1. Streamlit UI 시작
# 페이지 설정
st.set_page_config(layout="wide")

# 상단 제목 영역 (회색 배경 + 흰 글씨)
st.markdown("""
    <div style='background-color: #4D4D4D; padding: 20px; border-radius: 8px;'>
        <h1 style='color: white; text-align: center; margin: 0;'> 이상치 탐지 모니터링</h1>
        <p style='color: white; text-align: center; font-size: 16px;'>예측 결과 및 이상치 경보를 확인하세요.</p>
    </div>
""", unsafe_allow_html=True)

# 2. 파일 매핑
hospital_file_map = {
    "CRE(충북대병원)": ("CRE(충북대)_경보결과.xlsx", "CRE(충북대병원) 이상치 탐지", "CRE 발생 건수"),
    "표본감시(충북대병원)": ("표본감시(충북대)_경보결과.xlsx", "표본감시(충북대병원) 이상치 탐지", "표본감시 발생 건수")
}

community_file_map = {
    "CRE(전국)": ("CRE(전국)_경보결과.xlsx", "CRE(전국) 이상치 탐지", "CRE 발생 건수"),
    "CRE(충북)": ("CRE(충북)_경보결과.xlsx", "CRE(충북) 이상치 탐지", "CRE 발생 건수"),
    "표본감시(전국)": ("표본감시(전국)_경보결과.xlsx", "표본감시(전국) 이상치 탐지", "표본감시 발생 건수"),
    "표본감시(충북)": ("표본감시(충북)_경보결과.xlsx", "표본감시(충북) 이상치 탐지", "표본감시 발생 건수")
}

# 3. 시각화 함수
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

    # 이상치 (경보) 시각화
    outlier_label_added = False
    if '경보' in df.columns:
        try:
            df['경보'] = df['경보'].apply(
                lambda x: True if str(x).strip().upper() in ['TRUE', '1', '1.0', 'T'] else False
            )
            outlier_rows = df[df['경보']]
            for _, row in outlier_rows.iterrows():
                edge_color = 'black' if row['ds'] == current_date else 'gray'
                ax.plot(row['ds'], row['y'], marker='*', color='#FFC107', markersize=6,
                        markeredgecolor=edge_color,
                        label='이상치' if not outlier_label_added else None)
                outlier_label_added = True
        except Exception as e:
            st.error(f"⚠️ 이상치 시각화 오류: {e}")

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
    order = ['신뢰구간(95%)', f'실제 {y_label}', 'One-step 예측', '이상치', '예측 시작']
    ordered_handles = [label_handle_map[lbl] for lbl in order if lbl in label_handle_map]
    ordered_labels = [lbl for lbl in order if lbl in label_handle_map]

    ax.legend(ordered_handles, ordered_labels,
              fontsize=3, markerscale=0.7, loc='upper left', frameon=False, prop=fontprop)

    st.pyplot(fig)


# 4. 경보 탑지 함수
def render_alarms(alarm_records, current_date):
    st.markdown("### 🙎️ 경보 내역")

    for name, raw_df in alarm_records:
        st.markdown(f"#### 📌 {name}")

        if '경보' not in raw_df.columns:
            st.warning("⚠️ '경보' 컬럼 없음")
            continue

        try:
            raw_df['경보'] = raw_df['경보'].apply(
                lambda x: True if str(x).strip().upper() in ['TRUE', '1', '1.0', 'T'] else False
            )
            alarm_df = raw_df[raw_df['경보']]
        except Exception as e:
            st.error(f"⚠️ 경보 컬럼 처리 중 오류 발생: {e}")
            continue

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
            st.markdown(f"<span style='font-size:13px;color:gray'>📍 현재({current_date.strftime('%Y-%m')})에는 경보가 없습니다.</span>", unsafe_allow_html=True)

        if not past_alarms.empty:
            st.markdown("과거 경보 내역")
            display_df = past_alarms[['ds', 'y', 'yhat_upper']].copy()
            display_df.columns = ['날짜', '실제값', '예측상한']
            display_df['날짜'] = display_df['날짜'].dt.strftime('%Y-%m')
            display_df['실제값'] = display_df['실제값'].astype(int)
            display_df['예측상한'] = display_df['예측상한'].round(2)
            st.table(display_df.reset_index(drop=True))
        else:
            st.markdown("과거 경보 내역 없음")

# 5. 경보 레벨 색상 매핑
level_color_map = {
    1: "Green",
    2: "Blue",
    3: "Yellow",
    4: "Orange",
    5: "Red"
}

# 6. 게이지 차트 함수
def draw_gauge(level, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=level,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "경보 레벨", 'font': {'size': 16}},
        gauge={
            'axis': {'range': [1, 5], 'tickmode': 'linear', 'dtick': 1},
            'bar': {'color': color},
            'steps': [
                {'range': [1, 2], 'color': "#00cc96"},
                {'range': [2, 3], 'color': "#636efa"},
                {'range': [3, 4], 'color': "#f4c430"},
                {'range': [4, 5], 'color': "#ffa15a"},
                {'range': [5, 5.1], 'color': "#ef553b"},
            ],
        }
    ))
    fig.update_layout(height=220, margin=dict(t=30, b=0, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)

# 7. 경보 레벨 판단 함수
def get_alarm_level(hospital_df, community_df, current_date):
    # 현재 날짜 기준으로 가장 최근 월 선택
    current_month = pd.to_datetime(current_date).strftime("%Y-%m")

    # 병원 경보 조건
    hospital_df["ds"] = pd.to_datetime(hospital_df["ds"])
    hospital_df["월"] = hospital_df["ds"].dt.strftime("%Y-%m")
    hosp_alarm = hospital_df[hospital_df["월"] == current_month]["경보"].values

    # 지역사회 경보 조건
    community_df["ds"] = pd.to_datetime(community_df["ds"])
    community_df["월"] = community_df["ds"].dt.strftime("%Y-%m")
    comm_alarm = community_df[community_df["월"] == current_month]["경보"].values

    hosp_alarm_bool = hosp_alarm[0] if len(hosp_alarm) > 0 else False
    comm_alarm_bool = comm_alarm[0] if len(comm_alarm) > 0 else False

    # 병원 2개월 연속 이상치 확인
    recent_hosp = hospital_df.sort_values("ds", ascending=False).head(2)
    two_month_alarm = (recent_hosp["경보"] == True).sum() >= 2

    if two_month_alarm:
        return 5
    elif hosp_alarm_bool and comm_alarm_bool:
        return 4
    elif hosp_alarm_bool:
        return 3
    elif comm_alarm_bool:
        return 2
    else:
        return 1

# 8. 3분할 레이아웃
left_panel, center_panel, right_panel = st.columns([1.1, 1.5, 1.5])

# 병원/지역사회 감염 선택값 초기화
hospital_choice = None
community_choice = None

# 👉 가운데: 병원 감염 드롭다운 + 예측 그래프
with center_panel:
    st.markdown("#### 🏥 병원 감염")
    hospital_choice = st.selectbox("병원 감염 선택", list(hospital_file_map.keys()))

# 👉 오른쪽: 지역사회 감염 드롭다운 + 예측 그래프
with right_panel:
    st.markdown("#### 🌐 지역사회 감염")
    community_choice = st.selectbox("지역사회 감염 선택", list(community_file_map.keys()))

# 👉 왼쪽: 통합 경보 영역
with left_panel:
    st.markdown("### 🔔 통합 경보")

    # 데이터 로드
    hospital_df = None
    community_df = None

    if hospital_choice and hospital_choice != "선택":
        file, title, ylabel = hospital_file_map[hospital_choice]
        if os.path.exists(file):
            hospital_df = pd.read_excel(file)
        else:
            st.warning(f"📁 병원 감염 파일({file})이 없습니다.")

    if community_choice and community_choice != "선택":
        file, title, ylabel = community_file_map[community_choice]
        if os.path.exists(file):
            community_df = pd.read_excel(file)
        else:
            st.warning(f"📁 지역사회 감염 파일({file})이 없습니다.")

    # 통합 경보 레벨 계산 및 게이지 표시
    if hospital_df is not None and community_df is not None:
        current_date = hospital_df['ds'].max()
        level = get_alarm_level(hospital_df, community_df, current_date)
        level_color_map = {
            1: 'green', 2: 'blue', 3: 'yellow', 4: 'orange', 5: 'red'
        }
        color = level_color_map[level]

        draw_gauge(level, color)
        st.markdown(f"#### 현재 레벨: {level}단계 ({color})")
    else:
        st.warning("📁 병원 또는 지역사회 경보 데이터가 부족합니다.")

    # 경보 레벨 설명 표
    st.markdown("###경보 레벨 체계 (5단계)")
    level_rows = [
        ("1단계", "안정", "🟢", "병원 감염 및 지역사회 감염 모두 안정"),
        ("2단계", "관찰", "🔵", "지역사회 감염 위험 존재"),
        ("3단계", "주의(경미)", "🟡", "병원 감염 이상치 1회"),
        ("4단계", "주의(강화)", "🟠", "병원 감염 이상치 1회 + 지역사회 감염 위험"),
        ("5단계", "경보", "🔴", "병원 감염 이상치 2개월 연속")
    ]
    st.markdown("""
    <style>
    .custom-table {
        border-collapse: collapse;
        width: 100%;
        font-size: 14px;
    }
    .custom-table td {
        border: 1px solid #ddd;
        padding: 6px;
    }
    </style>
    <table class="custom-table">
    """ + "".join([
        f"<tr>{''.join([f'<td>{cell}</td>' for cell in row])}</tr>" for row in level_rows
    ]) + "</table>", unsafe_allow_html=True)

# 병원 예측 그래프 표시
with center_panel:
    if hospital_df is not None:
        visualize_alert_graph(hospital_df, title="병원 감염 이상치 예측")
    else:
        st.info("병원 감염 데이터를 선택하세요.")

# 지역사회 예측 그래프 표시
with right_panel:
    if community_df is not None:
        visualize_alert_graph(community_df, title="지역사회 감염 이상치 예측")
    else:
        st.info("지역사회 감염 데이터를 선택하세요.")

# 9. 현재 날짜 설정
current_date = pd.to_datetime('2023-08-01')



