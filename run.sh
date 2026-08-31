#!/usr/bin/env bash
# 몸무게 기록 웹앱 실행 스크립트 (.venv 사용)
#
# 사용법:
#   ./run.sh              # 기본 포트 8077
#   ./run.sh 9000         # 포트 지정
#   PORT=9000 ./run.sh    # 환경변수로 포트 지정
#
# 같은 디렉터리의 .env 파일이 있으면 자동으로 읽어서 환경변수로 주입합니다.
#   ENV_FILE=.env.prod ./run.sh   # 다른 파일 사용

set -euo pipefail

# 스크립트 위치 기준으로 이동 (어디서 실행하든 동작)
cd "$(dirname "$0")"

# .env 로드 (있으면). 이미 셸에 설정된 환경변수가 .env 값보다 우선합니다.
ENV_FILE="${ENV_FILE:-.env}"
if [ -f "$ENV_FILE" ]; then
  echo "환경변수 로드: $ENV_FILE"
  while IFS= read -r line || [ -n "$line" ]; do
    # 주석/빈 줄 건너뛰기
    case "$line" in ''|'#'*) continue ;; esac
    # 앞의 export 접두어 제거
    line="${line#export }"
    key="${line%%=*}"
    val="${line#*=}"
    # KEY=VALUE 형태가 아니면 무시
    case "$key" in *[!A-Za-z0-9_]*|'') continue ;; esac
    # 값 앞뒤 따옴표 제거
    case "$val" in
      \"*\") val="${val#\"}"; val="${val%\"}" ;;
      \'*\') val="${val#\'}"; val="${val%\'}" ;;
    esac
    # 이미 설정된 환경변수는 덮어쓰지 않음
    if [ -z "${!key:-}" ]; then
      export "$key=$val"
    fi
  done < "$ENV_FILE"
fi

PYTHON=".venv/bin/python"
PORT="${1:-${PORT:-8077}}"
HOST="${HOST:-0.0.0.0}"

if [ ! -x "$PYTHON" ]; then
  echo "오류: $PYTHON 를 찾을 수 없습니다. 이 프로젝트의 .venv 가 필요합니다." >&2
  exit 1
fi

# 같은 네트워크의 폰에서 접속할 IP 안내
LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || true)"
echo "몸무게 기록 웹앱 시작..."
echo "  로컬:   http://localhost:${PORT}"
if [ -n "$LAN_IP" ]; then
  echo "  같은 와이파이(폰 등): http://${LAN_IP}:${PORT}"
fi
echo "  종료: Ctrl+C"
echo

exec "$PYTHON" -m uvicorn app:app --host "$HOST" --port "$PORT"
