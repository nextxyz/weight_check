# Weight Check ⚖️ (직접 입력 버전)

몸무게를 **직접 입력**해 기록하고, 시간에 따른 변화를 **그래프**로 보여주는 초경량 웹앱입니다.

원본 프로젝트([`../OCR-weight-check`](../OCR-weight-check))는 체중계 사진을 찍어 OCR로 숫자를 인식했지만,
OCR 모듈(`easyocr`/`torch`/`opencv`)이 무거워 작은 서버에 올리기 어려웠습니다.
이 버전은 **OCR을 제거하고 사용자가 값을 직접 입력**하도록 바꿔, 순수 파이썬 의존성만으로 동작합니다.

- 🪶 **초경량** — `fastapi` + `uvicorn` 만 필요 (torch/easyocr/opencv/numpy 전부 제거)
- ⌨️ 몸무게 입력 → 저장 (시간은 비워두면 현재 시각, 원하면 직접 지정)
- 📈 Chart.js 라인차트 (X축: 기록 시간, Y축: 몸무게)
- 💾 SQLite 파일 1개(`weights.db`)에 기록 저장

## 설치

Python 3.10+ 권장.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 실행

```bash
./run.sh              # 기본 포트 8077
./run.sh 9000         # 포트 지정
```

또는 직접:

```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8077
```

브라우저에서 `http://localhost:8077` 접속. 같은 와이파이의 휴대폰에서 접속하려면 실행 시 출력되는 LAN 주소(`http://<PC_IP>:8077`)를 사용하세요.

## 구조

```
app.py             FastAPI 앱: API + HTML 서빙
db.py              SQLite 저장소
static/index.html  프론트엔드 (입력 폼 + Chart.js)
run.sh             실행 스크립트 (.venv 사용)
```

### API

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET`  | `/` | 웹 페이지 |
| `POST` | `/api/measurements` | `{weight, taken_at?}` 저장 (시간 생략 시 현재 시각) |
| `GET`  | `/api/measurements` | 기록 전체(JSON) |
| `PATCH`| `/api/measurements/{id}` | 기록의 몸무게 수정 |
| `DELETE`| `/api/measurements/{id}` | 기록 삭제 |

## 인증 (선택)

환경변수 `BASIC_AUTH_USER` / `BASIC_AUTH_PASS` 를 모두 설정하면 전체 요청에 HTTP Basic 인증이 걸립니다.
미설정 시 인증 없이 동작합니다. 외부에 오픈할 때는 HTTPS(리버스 프록시)와 함께 사용하세요.

```bash
BASIC_AUTH_USER=me BASIC_AUTH_PASS=secret ./run.sh
```

## Docker 배포 (레지스트리 없이)

개인 프로젝트라 별도 레지스트리가 없을 때, 이미지를 `tar.gz`로 추출해 다른 서버로 옮겨 띄웁니다.

**빌드 머신(예: 개발 PC)에서:**
```bash
./deploy.sh                       # linux/amd64 서버용 (일반적)
PLATFORM=linux/arm64 ./deploy.sh  # arm64 서버면
```
→ `weight-check.tar.gz` 생성. (⚠ 빌드 플랫폼과 서버 CPU 아키텍처가 일치해야 함)

**배포 서버에서:**
```bash
gunzip -c weight-check.tar.gz | docker load
docker run -d --name weightcheck \
  -p 8077:8077 \
  -v $PWD/data:/data \
  --restart unless-stopped \
  weight-check:latest
```
→ `http://서버IP:8077`

### docker compose 로 띄우기 (더 간단)

```bash
# 빌드 호스트(소스 있음): 빌드 후 실행
docker compose up -d --build

# 배포 서버(tar.gz 로드 후): 로드된 이미지로 실행
gunzip -c weight-check.tar.gz | docker load
docker compose up -d

docker compose logs -f      # 로그 보기
docker compose down         # 중지/삭제 (data/ 는 보존)
```

데이터는 `./data` 폴더의 `weights.db`에 저장되고, 포트·경로는 `docker-compose.yml`에서 조정합니다.
OCR 버전과 달리 모델 다운로드가 없어 이미지 크기가 수십 MB 수준으로 작고 빌드도 빠릅니다.

## 라이선스

MIT
