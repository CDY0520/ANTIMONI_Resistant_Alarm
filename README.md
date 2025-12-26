# ANTI MONI: 감염병 모니터링 서비스 개발 프로젝트
(자연어처리 기반 검사 판독문 분석을 통한 감염병 모니터링 시스템 구축)

프로젝트 기간: 2025.06.27 ~ 2025.07.31 (총 5주)
팀 구성: 5명 (DB 1, NLP 1, 내부모델 1, 외부모델 1, 대시보드·UI 1)
역할: 모델링 및 경보 대시보드 주도 (기여도 ★★★★☆)

---

# 프로젝트 개요

목적
검사 판독문을 자연어처리하여 감염병 발생 건수를 추출하고,
Prophet 기반 시계열 예측 모델을 통해 이상 발생을 조기 탐지하여
의료진이 실시간으로 대응할 수 있는 감염병 모니터링 시스템을 구축한다.

해결 방안 (Solution)
Prophet 기반 시계열 예측 모델을 통해 내부 감염 건수를 예측
예측값과 실제 발생값을 비교하여 이상치 자동 탐지 로직 설계
결과에 따라 1~5단계 경보 시스템 적용
Streamlit 대시보드를 활용한 실시간 시각화 및 경보 현황 제공

---

# 주요 기능
데이터 전처리 (preprocessing):	감염 건수 집계, 결측치 처리, 최초 분리균(first isolation) 기준 정제
예측 모델 (predictive_model):	Prophet 모델 기반 감염 발생 예측 및 이상치 탐지
상관 분석 (analysis):	단계예측에 사용할 외부 데이터와 내부 데이터 간 상관관계 분석 및 변수 선택 실험
알람 대시보드 (alarm_dashboard):	Streamlit 기반 경보 시스템 및 시각화 UI
입력 데이터 (input_data):	예측 결과 및 경보 레벨이 반영된 엑셀 데이터

---

# 폴더 구조

```
ANTI_MONI_Resistant_Alarm/
│
├── alarm_dashboard/           Streamlit 대시보드 코드, 대시보드 input 데이터
│   ├── stream_app.py
|   ├── CRE(병원내부)_경보결과.xlsx
│   ├── CRE(전국)_경보결과.xlsx
│   ├── CRE(충북)_경보결과.xlsx
│   └── 표본감시(병원내부)_경보결과.xlsx
│   └── 통합 경보 레벨 설명표.xlsx
│
├── analysis/                  상관분석 및 변수 선택 코드
│   ├── CRE_prophet_변수선택.py
│   ├── 상관분석_CRE.py
│   ├── 상관분석_표본감시.py
│   └── 표본감시_변수선택.py
│
├── predictive_model/          Prophet 기반 예측 모델 코드, 모델 input 데이터
│   ├── CRE_prophet.py
│   └── 표본감시_prophet.py
│
├── preprocessing/             데이터 전처리 코드
│   ├── 감염_카운트_first isolation_연도별.py
│   ├── 전체결측_통계.py
│   ├── 원데이터에서 데이터 정제(isolation).py
|   ├── 표본감시_카운트_first isolation.py
|   ├── 표본감시_내부.sql       데이터베이스에서 내부데이터 로딩하는 sql코드
|   ├── CRE_내부.sql
│   └── FOR_PREDICT.sql
│
├── fonts/                     시각화용 한글 폰트
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

# 성능 지표 (Performance Metrics)

모델 예측 성능 평가는 다음 세 가지 지표로 수행되었다.
MAE (Mean Absolute Error)
RMSE (Root Mean Square Error)
MAPE (Mean Absolute Percentage Error)      메인으로 참고

---

# 역할 요약 (My Role)

외부 감염병 데이터 수집 및 전처리
Prophet 기반 시계열 예측 및 이상치 탐지 모델 개발
경보 시스템 규칙 및 성능지표(MAE, RMSE, MAPE) 설계
Streamlit 대시보드 UX/UI 설계 및 구현
사용자 중심 정보전달 방식 기획

---

# 참고

통합 경보 단계 기준: 통합경보 1~5단계 (병원·지역사회 이상치 조합에 따른 단계별 규칙 적용)
대시보드 목적: 의료진이 실시간으로 이상 발생을 인지하고 대응할 수 있도록 경보 시각화 중심으로 구성됨.

