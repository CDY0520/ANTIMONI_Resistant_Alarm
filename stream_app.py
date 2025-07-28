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

# 제목 박스: 사용자 정의 배경색 + 중앙 정렬 텍스트
st.markdown(
    """
    <div style="background-color: #2B3F73; padding: 20px; border-radius: 10px; text-align: center;">
        <h1 style="color: white; font-family: 'Noto Sans KR', sans-serif;">이상치 탐지 모니터링</h1>
        <p style="color: white; font-size: 18px;">예측 결과 및 이상치 경보를 확인하세요.</p>
    </div>
    """,
    unsafe_allow_html=True
)

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

    df = df[df['ds'].dt.year == 2023]
    past_mask = df['ds'] < current_date
    current_mask = df['ds'] == current_date

    fig, ax = plt.subplots(figsize=(7, 3))
    fig.patch.set_facecolor('#FFF7F0')

    # 신뢰구간
    ax.fill_between(df['ds'], df['yhat_lower'], df['yhat_upper'],
                    where=~df['yhat_lower'].isna(),
                    color='red', alpha=0.2, label='신뢰구간(95%)')

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
    ax.plot([], [], marker='*', color='#FFC107', markersize=6, linestyle='None', label='이상치')  # 범례 고정용
    outlier_label_added = False

    try:
        df['경보'] = df['경보'].apply(lambda x: True if str(x).strip().upper() in ['TRUE', '1', '1.0', 'T'] else False)
        outlier_rows = df[df['경보']]
        for _, row in outlier_rows.iterrows():
            edge_color = 'black' if row['ds'] == current_date else 'gray'
            if not outlier_label_added:
                ax.plot(row['ds'], row['y'], marker='*', color='#FFC107', markersize=6,
                        markeredgecolor=edge_color, markeredgewidth=0.8, label='이상치')
                outlier_label_added = True
            else:
                ax.plot(row['ds'], row['y'], marker='*', color='#FFC107', markersize=6,
                        markeredgecolor=edge_color, markeredgewidth=0.8)
    except Exception as e:
        st.error(f"⚠️ 이상치 시각화 오류: {e}")

    ax.axvline(current_date, color='gray', linestyle='--', linewidth=0.8, label='예측 시작')

    ax.set_title(title_text, fontsize=7, fontproperties=fontprop)
    ax.set_xlabel("날짜", fontsize=6, fontproperties=fontprop)
    ax.set_ylabel(y_label, fontsize=6, fontproperties=fontprop)
    ax.tick_params(axis='both', labelsize=5, colors='#2B2D42')
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    ax.grid(True, linestyle='--', linewidth=0.4, color='#CCCCCC')

    # 범례 정렬
    handles, labels = ax.get_legend_handles_labels()
    label_handle_map = dict(zip(labels, handles))
    order = ['신뢰구간(95%)', f'실제 {y_label}', 'One-step 예측', '이상치', '예측 시작']
    ordered_handles = [label_handle_map[lbl] for lbl in order if lbl in label_handle_map]
    ordered_labels = [lbl for lbl in order if lbl in label_handle_map]

    ax.legend(ordered_handles, ordered_labels,
              fontsize=6, markerscale=0.6, loc='upper left', frameon=False, prop=fontprop)

    st.pyplot(fig)

# 4. 시각화 래퍼 함수
def visualize_alert_graph(df, title="이상치 예측"):
    import matplotlib.pyplot as plt
    import pandas as pd

    fig, ax = plt.subplots(figsize=(7, 3))
    fig.patch.set_facecolor('#FFF7F0')

    # 라인 플롯
    ax.plot(df['ds'], df['y'], label='실제 예측값', marker='o', color='royalblue', linewidth=1, markersize=3)
    ax.plot(df['ds'], df['yhat1'], label='One-step 예측', linestyle='--', color='red', linewidth=1, markersize=3)

    # 신뢰구간
    ax.fill_between(df['ds'], df['yhat1_lower'], df['yhat1_upper'],
                    where=~df['yhat1_lower'].isna(),
                    color='red', alpha=0.2, label='신뢰구간 (95%)')

    # 예측 시작선
    if '예측시작' in df.columns and df['예측시작'].notna().any():
        try:
            start_date = pd.to_datetime(df['예측시작'].dropna().values[0])
            ax.axvline(start_date, linestyle='--', color='gray', linewidth=0.8, label='예측 시작')
        except Exception as e:
            st.warning(f"예측시작 처리 오류: {e}")

    # 이상치 별표
    outlier_label_added = False
    if '경보' in df.columns:
        df['경보'] = df['경보'].apply(lambda x: True if str(x).strip().upper() in ['TRUE', '1', '1.0', 'T'] else False)
        for _, row in df[df['경보']].iterrows():
            label = '이상치' if not outlier_label_added else None
            ax.plot(row['ds'], row['y'], marker='*', color='#FFC107', markersize=10,
                    markeredgecolor='black', markeredgewidth=0.6, linestyle='None', label=label)
            outlier_label_added = True

    # 스타일 및 라벨
    ax.set_title(title, fontsize=8, fontproperties=fontprop)
    ax.set_xlabel("날짜", fontsize=7, fontproperties=fontprop)
    ax.set_ylabel("예측값", fontsize=7, fontproperties=fontprop)
    ax.tick_params(axis='both', labelsize=6)
    ax.grid(True, linestyle='--', linewidth=0.5, color='#CCCCCC')

    # 범례
    ax.legend(fontsize=6, loc='upper left', frameon=False, prop=fontprop)

    st.pyplot(fig)

# 5. 경보 탑지 함수
def render_alarms(df, panel_title="경보 내역"):
    st.markdown(f"### {panel_title}")
    if df.empty:
        st.info("📌 현재 경보가 없습니다.")
        return

    df = df.copy()

    # 날짜 및 수치 포맷
    if '날짜' in df.columns:
        df['날짜'] = pd.to_datetime(df['날짜']).dt.strftime('%Y-%m-%d')

    for col in ['예측값', '예측하한', '예측상한', '실제값']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "")

    # 컬럼 순서 명시 (원하는 컬럼으로 조정)
    expected_cols = ['날짜', '예측값', '예측하한', '예측상한', '실제값', '경보해석']
    df = df[[col for col in expected_cols if col in df.columns]]

    # 커스텀 테이블 스타일
    st.markdown("""
    <style>
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        font-family: 'Noto Sans KR', sans-serif;
        background-color: #F9FAFB;
        border: 1px solid #DDD;
    }
    .custom-table th {
        background-color: #2B3F73;
        color: white;
        padding: 6px;
        border: 1px solid #DDD;
    }
    .custom-table td {
        text-align: center;
        padding: 6px;
        border: 1px solid #DDD;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(df.to_html(index=False, classes='custom-table'), unsafe_allow_html=True)

# 6. 경보 레벨 색상 매핑
level_color_map = {
    1: "#00cc96",  # Green
    2: "#636efa",  # Blue
    3: "#f4c430",  # Yellow
    4: "#ffa15a",  # Orange
    5: "#ef553b"   # Red
}

# 7. 게이지 차트 함수
def draw_gauge(level, color_hex=None):
    # 값 체크
    if level < 1 or level > 5:
        st.error("경보 레벨은 1~5 사이여야 합니다.")
        return

    # 색상 설정 (사용자가 따로 color_hex를 넘기지 않아도 내부에서 결정)
    level_colors = ['#00cc96', '#636efa', '#f4c430', '#ffa15a', '#ef553b']
    level_labels = ['1', '2', '3', '4', '5']

    # 반원 게이지 구성 (go.Pie)
    fig = go.Figure()

    fig.add_trace(go.Pie(
        values=[20] * 5 + [100],  # 5개 구간 + 투명한 아래쪽
        rotation=180,
        hole=0.6,
        direction='clockwise',
        text=level_labels + [''],
        textinfo='text',
        textposition='inside',
        marker_colors=level_colors + ['rgba(0,0,0,0)'],
        hoverinfo='skip',
        showlegend=False
    ))

    # 바늘 좌표 계산
    angle_deg = 180 - (level - 1) * 36 - 18  # 중앙 기준 각도
    angle_rad = np.radians(angle_deg)
    x = 0.5 + 0.4 * np.cos(angle_rad)
    y = 0.5 + 0.4 * np.sin(angle_rad)

    # 바늘 추가
    fig.add_shape(type='line',
        x0=0.5, y0=0.5, x1=x, y1=y,
        line=dict(color='black', width=4)
    )

    # 중앙 숫자 표시
    fig.add_annotation(
        text=f"<b>{level}</b>", x=0.5, y=0.5,
        font=dict(size=36, color='white', family='Noto Sans KR'),
        showarrow=False
    )

    fig.update_layout(
        height=300,
        margin=dict(t=30, b=0, l=10, r=10),
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117'
    )

    st.plotly_chart(fig, use_container_width=True)

# 8. 경보 레벨 판단 함수
def get_alarm_level(hospital_df, community_df, current_date):
    current_month = pd.to_datetime(current_date).strftime("%Y-%m")

    # 병원 데이터 처리
    hospital_df = hospital_df.copy()
    hospital_df["ds"] = pd.to_datetime(hospital_df["ds"])
    hospital_df["월"] = hospital_df["ds"].dt.strftime("%Y-%m")
    hospital_df["경보"] = hospital_df["경보"].apply(lambda x: str(x).strip().upper() in ["TRUE", "1", "1.0", "T"])

    # 지역사회 데이터 처리
    community_df = community_df.copy()
    community_df["ds"] = pd.to_datetime(community_df["ds"])
    community_df["월"] = community_df["ds"].dt.strftime("%Y-%m")
    community_df["경보"] = community_df["경보"].apply(lambda x: str(x).strip().upper() in ["TRUE", "1", "1.0", "T"])

    # 현재 월 기준 경보 여부
    hosp_alarm_bool = hospital_df[hospital_df["월"] == current_month]["경보"].any()
    comm_alarm_bool = community_df[community_df["월"] == current_month]["경보"].any()

    # 최근 2개월 병원 경보 여부 확인
    recent_hosp = hospital_df.sort_values("ds", ascending=False).head(2)
    two_month_alarm = recent_hosp["경보"].sum() >= 2

    # 경보 레벨 판정
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
        current_date = hospital_df['ds'].max() if 'ds' in hospital_df.columns else pd.to_datetime("2023-08-01")
        level = get_alarm_level(hospital_df, community_df, current_date)
        draw_gauge(level, level_color_map[level])
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

# 👉 병원 예측 그래프 및 경보 내역
with center_panel:
    st.markdown("### 병원 감염 이상치 예측")
    if hospital_df is not None:
        visualize_alert_graph(hospital_df, title="병원 감염 이상치 예측")
        hospital_alert_df = hospital_df[hospital_df["경보"] == True] if "경보" in hospital_df.columns else pd.DataFrame()
        render_alarms(hospital_alert_df, panel_title="과거 경보 내역")

# 👉 지역사회 예측 그래프 및 경보 내역
with right_panel:
    st.markdown("### 지역사회 감염 이상치 예측")
    if community_df is not None:
        visualize_alert_graph(community_df, title="지역사회 감염 이상치 예측")
        community_alert_df = community_df[community_df["경보"] == True] if "경보" in community_df.columns else pd.DataFrame()
        render_alarms(community_alert_df, panel_title="과거 경보 내역")

# 10. 현재 날짜 설정
current_date = pd.to_datetime('2023-08-01')



