# 0. 라이브러리 임포트 및 설정
import streamlit as st
import pandas as pd
import numpy as np
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

# 3. 현재 날짜 설정 및 data_dict 정의
current_date = pd.to_datetime('2023-08-01')
data_dict = {}

for name, (filename, _, _) in hospital_file_map.items():
    filepath = filename
    if os.path.exists(filepath):
        df = pd.read_excel(filepath)
        df['ds'] = pd.to_datetime(df['ds'])
        data_dict[name] = df
    else:
        pass

for name, (filename, _, _) in community_file_map.items():
    filepath = filename
    if os.path.exists(filepath):
        df = pd.read_excel(filepath)
        df['ds'] = pd.to_datetime(df['ds'])
        data_dict[name] = df
    else:
        pass
        
# 4. 시각화 함수
def plot_graph(df, title_text, y_label, current_date):
    df = df[df['ds'].dt.year == 2023]
    past_mask = df['ds'] < current_date
    current_mask = df['ds'] == current_date

    fig, ax = plt.subplots(figsize=(7, 3))
    
    # 배경색 적용
    fig.patch.set_facecolor("#fef9f5")
    ax.set_facecolor("#fef9f5")

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

# 6. 경보 메시지 관련 함수
# 경보 탑지 함수
def render_alert_message(latest_df, current_date, dataset_label="병원 감염"):
    """
    이상치 발생 여부에 따라 경보 메시지 출력.
    latest_df: 최신 월 데이터 (df.tail(1) 또는 마지막 달 필터된 df)
    current_date: 기준이 되는 현재 날짜
    dataset_label: "병원 감염" / "지역사회 감염"
    """
    row = latest_df.iloc[0]
    current_date_str = pd.to_datetime(current_date).strftime("%Y-%m")

    # 경보 여부 확인 (문자열일 가능성 포함하여 처리)
    is_alert = str(row.get('경보', '')).strip().upper() in ["TRUE", "1", "1.0", "T"]

    if is_alert:
        try:
            current_val = int(row['y']) if pd.notna(row['y']) else "값 없음"
            upper_val = round(float(row['yhat_upper']), 2) if pd.notna(row['yhat_upper']) else "값 없음"
            interpretation = row.get('경보해석', '')
        except Exception as e:
            st.error(f"⚠️ 경보 메시지 처리 오류: {e}")
            return

        message_md = f"""
        <div style="background-color:#fcf8f2; padding:10px; border-radius:8px;">
            <span style="color:#FF4B4B; font-weight:bold;">📌 [{current_date_str}] {dataset_label} 이상치 발생</span><br>
            <span style="color:black;">▶ 현재값 ({current_val})이 예측 상한값 ({upper_val})을 초과하였습니다.</span><br>
            <span style="color:black;">▶ {interpretation}</span>
        </div>
        """
        st.markdown(message_md, unsafe_allow_html=True)

    else:
        message_md = f"""
        <div style="background-color:#fcf8f2; padding:10px; border-radius:8px;">
            <span style="color:#FF4B4B; font-weight:bold;">📌 [{current_date_str}] 현재 이상치가 발생하지 않아 경보가 없습니다.</span>
        </div>
        """
        st.markdown(message_md, unsafe_allow_html=True)

# 과거 경보 테이블 표시 함수
def display_alert_table(df):
    """
    과거 경보 내역을 테이블로 표시합니다.
    """
    df = df.copy()
    df['ds'] = pd.to_datetime(df['ds'])
    df['월'] = df['ds'].dt.strftime("%Y-%m")

    df['경보'] = df['경보'].apply(lambda x: str(x).strip().upper() in ["TRUE", "1", "1.0", "T"])

    alert_df = df[df['경보']].copy()
    alert_df = alert_df[['월', 'y', 'yhat_upper']].rename(columns={
        '월': '경보 발생 시점',
        'y': '현재값',
        'yhat_upper': '예측 상한값'
    })

    alert_df['현재값'] = alert_df['현재값'].astype(int)
    alert_df['예측 상한값'] = alert_df['예측 상한값'].round(2)

    if alert_df.empty:
        st.info("📭 과거 경보 내역이 없습니다.")
    else:
        styled_table = (
            alert_df.style
            .format({'예측 상한값': '{:.2f}'})  # 소수점 2자리
            .set_properties(**{'text-align': 'center'})  # 셀 가운데 정렬
            .set_table_styles([
                {'selector': 'th', 'props': [('text-align', 'center')]}  # 컬럼명 가운데 정렬
            ])
        )
        st.dataframe(styled_table, use_container_width=True, hide_index=True)


# 7. 경보 레벨 색상 매핑
level_color_map = {
    1: "#00cc96",  # Green
    2: "#636efa",  # Blue
    3: "#f4c430",  # Yellow
    4: "#ffa15a",  # Orange
    5: "#ef553b"   # Red
}

# 8. 게이지 차트 함수
def draw_gauge(level, color_hex=None):
    # 값 체크
    if level < 1 or level > 5:
        st.error("경보 레벨은 1~5 사이여야 합니다.")
        return

    # 색상 설정
    level_colors = ['#00cc96', '#636efa', '#f4c430', '#ffa15a', '#ef553b']
    level_labels = ['1', '2', '3', '4', '5']

    # 반원 게이지 구성 (go.Pie)
    fig = go.Figure()
    
    fig.add_trace(go.Pie(
        values=[20] * 5 + [100],
        rotation=-270,
        hole=0.6,
        direction='clockwise',
        text=level_labels + [''],
        textinfo='text',
        textposition='inside',
        marker_colors=level_colors + ['rgba(0,0,0,0)'],
        hoverinfo='skip',
        showlegend=False
    ))

    # 바늘 좌표 계산 (가운데서 시작해서 해당 레벨 위치로)
    angle_deg = 180 - (level - 1) * 36 - 18  # 각도 (중앙값 기준)
    angle_rad = np.radians(angle_deg)
    x = 0.5 + 0.28 * np.cos(angle_rad)
    y = 0.5 + 0.28 * np.sin(angle_rad)

    # 바늘 (흰색 선)
    fig.add_shape(type='line',
        x0=0.5, y0=0.5, x1=x, y1=y,
        line=dict(color='white', width=4)
    )

    # 바늘 각도 조정: 180도 기준에서 시계방향 36도씩 이동
    angle_deg = 180 - (level - 1) * 36 - 18
    angle_rad = np.radians(angle_deg)

    # 바늘 길이 짧게 (0.3), 시작점 0.5 → 중심에서 시작
    x = 0.5 + 0.3 * np.cos(angle_rad)
    y = 0.5 + 0.3 * np.sin(angle_rad)

    fig.add_shape(
        type='line',
        x0=0.5, y0=0.5, x1=x, y1=y,
        line=dict(color='white', width=4)
    )

    # 중앙 숫자 약간 아래로 이동 (y=0.44)
    fig.add_annotation(
        text=f"<b>{level}</b>",
        x=0.5, y=0.42,
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

# 9. 경보 레벨 판단 함수
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

# current_date 매번 외부에서 받도록 설정
def get_integrated_alert_level(hospital_df, community_df, current_date):
    level = get_alarm_level(hospital_df, community_df, current_date)
    color_hex = level_color_map.get(level, "#000000")
    return level, color_hex

# 10. 3분할 레이아웃
col1, col2, col3 = st.columns([1.1, 1.5, 1.5])

# ------------------------
# ✅ col2: 병원 감염 영역
# ------------------------
with col2:
    st.markdown("### 🏥 병원 감염 선택")

    # 감염 종류 선택 (선택 옵션 추가)
    hospital_options = ["선택"] + list(hospital_file_map.keys())
    hospital_choice = st.selectbox("", hospital_options, index=0, key="hospital_select")

    if hospital_choice != "선택":
        hospital_df = data_dict[hospital_choice]
        y_label_hospital = hospital_file_map[hospital_choice][2]

        # 병원 감염 그래프
        plot_graph(
            df=hospital_df,
            title_text="병원 감염 이상치 예측",
            y_label=y_label_hospital,
            current_date=current_date
        )

        # 현재 경보 메시지
        latest_hosp = hospital_df[hospital_df['ds'] == hospital_df['ds'].max()]
        render_alert_message(latest_hosp, current_date, dataset_label="병원 감염")

        # 과거 경보 내역
        st.markdown("### 과거 경보 내역")
        display_alert_table(hospital_df)

# ------------------------
# ✅ col3: 지역사회 감염 영역
# ------------------------
with col3:
    st.markdown("### 🌐 지역사회 감염 선택")

    community_options = ["선택"] + list(community_file_map.keys())
    community_choice = st.selectbox("", community_options, index=0, key="community_select")

    if community_choice != "선택":
        community_df = data_dict[community_choice]
        y_label_community = community_file_map[community_choice][2]

        # 지역사회 감염 그래프
        plot_graph(
            df=community_df,
            title_text="지역사회 감염 이상치 예측",
            y_label=y_label_community,
            current_date=current_date
        )

        # 현재 경보 메시지
        latest_comm = community_df[community_df['ds'] == community_df['ds'].max()]
        render_alert_message(latest_comm, current_date, dataset_label="지역사회 감염")

        # 과거 경보 내역
        st.markdown("### 과거 경보 내역")
        display_alert_table(community_df)
        
# ------------------------
# ✅ col1: 통합 경보 영역 (hospital_df & community_df 정의 이후로 이동)
# ------------------------
with col1:
    st.markdown("### 🔔 통합 경보")
    st.markdown("#### ")

    if (
        'hospital_df' in locals() and hospital_choice != "선택" and
        'community_df' in locals() and community_choice != "선택"
    ):
        level, color_hex = get_integrated_alert_level(hospital_df, community_df, current_date)

        # 바늘형 게이지 차트 시각화
        draw_gauge(level, color_hex)

        # 경보 체계 설명표
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


