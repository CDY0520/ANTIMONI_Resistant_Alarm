FROM python:3.10-slim

# (선택) 폰트/빌드 관련 기본 패키지
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential fontconfig \
    && rm -rf /var/lib/apt/lists/*

# 1) 작업 폴더
WORKDIR /app

# 2) 의존성 먼저 설치 (캐시 효율)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) 프로젝트 전체 복사
COPY . .

# 4) (선택) 한글 폰트를 시스템 폰트로 등록 (fonts/ 폴더가 있을 때)
# 폰트 깨짐(□) 이슈 줄이는 데 도움됨
RUN if [ -d "fonts" ]; then \
      mkdir -p /usr/share/fonts/truetype/custom && \
      cp -r fonts/* /usr/share/fonts/truetype/custom/ && \
      fc-cache -fv; \
    fi

# 5) Streamlit 포트
EXPOSE 8501

# 6) 대시보드 폴더로 이동해서 실행 (상대경로 문제 예방)
WORKDIR /app/alarm_dashboard
CMD ["streamlit", "run", "stream_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
