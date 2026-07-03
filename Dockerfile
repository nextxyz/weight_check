# 초경량 몸무게 기록 웹앱 이미지 (OCR 없음 → 순수 파이썬 의존성만)
FROM python:3.12-slim

WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8077 \
    WEIGHT_DB=/data/weights.db

# 1) 의존성 먼저 설치 (레이어 캐시 활용)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 2) 앱 코드 복사
COPY . .

# 데이터(volume)는 /data 에 보관 → 컨테이너 재생성에도 보존
VOLUME ["/data"]
EXPOSE 8077

CMD ["sh", "-c", "python -m uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
