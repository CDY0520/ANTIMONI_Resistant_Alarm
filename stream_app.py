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

    # 2023년만 시각화
    df = df[df['ds'].dt.year == 2023]

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
    # 항상 범례에 나타내기 위한 빈 플롯
    ax.plot([], [], marker='*', color='#FFC107', markersize=6, linestyle='None', label='이상치')

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
              fontsize=1, markerscale=0.6, loc='upper left', frameon=False, prop=fontprop)

    st.pyplot(fig)

# 4. 시각화 래퍼 함수
def visualize_alert_graph(df, title="이상치 예측"):
    import matplotlib.pyplot as plt
    import numpy as np

    # fill_between 관련 열은 숫자형으로 변환
    df['yhat1_lower'] = pd.to_numeric(df['yhat1_lower'], errors='coerce')
    df['yhat1_upper'] = pd.to_numeric(df['yhat1_upper'], errors='coerce')

    # NaN 보간 (옵션: 필요한 경우만)
    df['yhat1_lower'].interpolate(method='linear', inplace=True)
    df['yhat1_upper'].interpolate(method='linear', inplace=True)

    plt.figure(figsize=(10, 5))
    plt.plot(df['ds'], df['y'], label='실제 예측값', marker='o', color='royalblue')
    plt.plot(df['ds'], df['yhat1'], label='One-step 예측', linestyle='--', color='red')

    # fill_between 적용 시 NaN 처리
    plt.fill_between(df['ds'], df['yhat1_lower'], df['yhat1_upper'],
                     where=~(df['yhat1_lower'].isna() | df['yhat1_upper'].isna()),
                     color='red', alpha=0.2)

    # 예측 시작선 표시
    if '예측시작' in df.columns:
        pred_start_dates = df['예측시작'].dropna().values
        if len(pred_start_dates) > 0:
            plt.axvline(pd.to_datetime(pred_start_dates[0]), linestyle='--', color='gray', label='예측 시작')

    # 이상치 별표 표시
    outlier_label_added = False
    for _, row in df.iterrows():
        if row.get('경보', False):
            label = '이상치' if not outlier_label_added else ""
            plt.plot(row['ds'], row['y'], marker='*', color='gold', markersize=12, label=label)
            outlier_label_added = True

    plt.legend(fontsize=9)
    plt.title(title)
    plt.xlabel("날짜")
    plt.ylabel("예측값")
    plt.grid(True)
    plt.tight_layout()
    st.pyplot(plt)


# 5. 경보 탑지 함수
def render_alarms(df, panel_title="경보 내역"):
    st.markdown(f"### {panel_title}")
    if df.empty:
        st.info("📌 현재 경보가 없습니다.")
        return

    # '예측상한' 소수점 둘째 자리로 포맷
    df = df.copy()
    df['예측상한'] = df['예측상한'].apply(lambda x: f"{x:.2f}")

    # HTML 테이블 가운데 정렬 및 스타일링
    st.markdown("""
    <style>
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }
    .custom-table th, .custom-table td {
        text-align: center;
        padding: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(df.to_html(index=False, classes='custom-table'), unsafe_allow_html=True)

# 6. 경보 레벨 색상 매핑
level_color_map = {
    1: "Green",
    2: "Blue",
    3: "Yellow",
    4: "Orange",
    5: "Red"
}

# 7. 게이지 차트 함수
def draw_gauge(level, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=level,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "현재 경보 레벨", 'font': {'size': 16}},
        gauge={
            'axis': {'range': [1, 6], 'tickmode': 'linear', 'dtick': 1},
            'bar': {'color': color},
            'steps': [
                {'range': [1, 2], 'color': "#00cc96"},
                {'range': [2, 3], 'color': "#636efa"},
                {'range': [3, 4], 'color': "#f4c430"},
                {'range': [4, 5], 'color': "#ffa15a"},
                {'range': [5, 6], 'color': "#ef553b"},
            ],
        }
    ))
    fig.update_layout(height=220, margin=dict(t=30, b=0, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)

# 8. 경보 레벨 판단 함수
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

# 9. 3분할 레이아웃
left_panel, center_panel, right_panel = st.columns([1.1, 1.5, 1.5])

# 👉 드롭다운 선택 (가운데/오른쪽)
with center_panel:
    st.markdown("### 🏥 병원 감염")
    hospital_choice = st.selectbox("병원 감염을 선택하세요", ["선택"] + list(hospital_file_map.keys()))

with right_panel:
    st.markdown("### 🌐 지역사회 감염")
    community_choice = st.selectbox("지역사회 감염을 선택하세요", ["선택"] + list(community_file_map.keys()))

# 👉 병원 및 지역사회 데이터 로딩
hospital_df = None
community_df = None

if hospital_choice != "선택":
    file_path = hospital_file_map[hospital_choice][0]
    if os.path.exists(file_path):
        hospital_df = pd.read_excel(file_path)
    else:
        st.warning(f"❌ 병원 감염 파일({file_path})이 존재하지 않습니다.")

if community_choice != "선택":
    file_path = community_file_map[community_choice][0]
    if os.path.exists(file_path):
        community_df = pd.read_excel(file_path)
    else:
        st.warning(f"❌ 지역사회 감염 파일({file_path})이 존재하지 않습니다.")

# 👉 왼쪽: 통합 경보 영역
with left_panel:
    st.markdown("### 🔔 통합 경보")

    if hospital_df is not None and community_df is not None:
        current_date = hospital_df['ds'].max()
        level = get_alarm_level(hospital_df, community_df, current_date)

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=level,
            title={'text': "경보 레벨", 'font': {'size': 20}},
            gauge={
                'axis': {'range': [1, 5], 'tickmode': 'array', 'tickvals': [1, 2, 3, 4, 5]},
                'bar': {'color': "black", 'thickness': 0.3},
                'steps': [
                    {'range': [1, 2], 'color': "#00cc96"},  # green
                    {'range': [2, 3], 'color': "#636efa"},  # blue
                    {'range': [3, 4], 'color': "#f4c430"},  # yellow
                    {'range': [4, 5], 'color': "#ffa15a"},  # orange
                    {'range': [5, 5.1], 'color': "#ef553b"} # red
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': level
                }
            }
        ))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("📌 병원 및 지역사회 감염 항목을 선택하세요.")

    # 경보 레벨 설명 표
    st.markdown("### 경보 레벨 체계 (5단계)")
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
        border: none;
        padding: 6px;
    }
    </style>
    <table class="custom-table">
    """ + "".join([
        f"<tr>{''.join([f'<td>{cell}</td>' for cell in row])}</tr>" for row in level_rows
    ]) + "</table>", unsafe_allow_html=True)

# 👉 병원 예측 그래프 표시
with center_panel:
    st.markdown("### 병원 감염 이상치 예측")
    if hospital_df is not None:
        visualize_alert_graph(hospital_df, title="병원 감염 이상치 예측")
        show_alert_table(hospital_alert_df, panel_title="과거 경보 내역")


# 👉 지역사회 예측 그래프 표시
with right_panel:
    st.markdown("### 지역사회 감염 이상치 예측")
    if community_df is not None:
        visualize_alert_graph(community_df, title="지역사회 감염 이상치 예측")
        show_alert_table(community_alert_df, panel_title="과거 경보 내역")


# 10. 현재 날짜 설정
current_date = pd.to_datetime('2023-08-01')



