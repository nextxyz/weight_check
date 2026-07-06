#!/usr/bin/env python
"""
몸무게 직접 입력 → 기록 → 그래프 웹앱 (FastAPI, 초경량).

OCR 버전(../OCR-weight-check)에서 무거운 의존성(torch/easyocr/opencv)을
모두 제거하고, 사용자가 몸무게를 직접 입력해 기록하도록 단순화한 버전.

흐름:
  1) /                       HTML 페이지 (입력 폼 + 차트)
  2) POST   /api/measurements       몸무게 값 저장
  3) GET    /api/measurements       기록 전체 (차트 데이터)
  4) PATCH  /api/measurements/{id}  기록의 몸무게 수정
  5) DELETE /api/measurements/{id}  기록 삭제
"""
from __future__ import annotations

import base64
import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

import db

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    print("준비 완료.")
    yield


app = FastAPI(title="Weight Check", lifespan=lifespan)


# ---------------------------------------------------------------------------
# HTTP Basic 인증
#   환경변수 BASIC_AUTH_USER / BASIC_AUTH_PASS 가 모두 설정되면 전체 요청을 보호한다.
#   (미설정 시 인증 없이 동작 — 로컬 개발 편의)
#   주의: Basic 인증은 자격증명을 매 요청마다 평문에 가깝게 전송하므로
#   외부 오픈 시 HTTPS(리버스 프록시) 사용을 권장한다.
# ---------------------------------------------------------------------------
BASIC_AUTH_USER = os.environ.get("BASIC_AUTH_USER")
BASIC_AUTH_PASS = os.environ.get("BASIC_AUTH_PASS")
_AUTH_ENABLED = bool(BASIC_AUTH_USER and BASIC_AUTH_PASS)
_UNAUTHORIZED = Response(
    status_code=401,
    content="인증이 필요합니다.",
    headers={"WWW-Authenticate": 'Basic realm="Weight Check"'},
)

if not _AUTH_ENABLED:
    print("경고: BASIC_AUTH_USER/BASIC_AUTH_PASS 미설정 - 인증 없이 동작합니다.")


def _check_basic_auth(header: str | None) -> bool:
    if not header or not header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(header[6:]).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return False
    user, sep, pw = decoded.partition(":")
    if not sep:
        return False
    # 타이밍 공격 방지를 위해 compare_digest 사용 (두 비교 모두 수행)
    user_ok = secrets.compare_digest(user, BASIC_AUTH_USER)
    pw_ok = secrets.compare_digest(pw, BASIC_AUTH_PASS)
    return user_ok and pw_ok


@app.middleware("http")
async def basic_auth_middleware(request: Request, call_next):
    if _AUTH_ENABLED and not _check_basic_auth(request.headers.get("Authorization")):
        return _UNAUTHORIZED
    return await call_next(request)


class MeasurementIn(BaseModel):
    weight: float
    taken_at: str | None = None  # 미지정 시 서버 현재시각


@app.post("/api/measurements")
async def create_measurement(m: MeasurementIn):
    """사용자가 입력한 몸무게를 저장한다."""
    if not (m.weight > 0):
        raise HTTPException(400, "올바른 몸무게가 아닙니다.")
    taken_at = m.taken_at or datetime.now().isoformat(timespec="seconds")
    row = db.add_measurement(weight=m.weight, taken_at=taken_at)
    return row


@app.get("/api/measurements")
async def get_measurements():
    return db.list_measurements()


class WeightUpdate(BaseModel):
    weight: float


@app.patch("/api/measurements/{measurement_id}")
async def update_measurement(measurement_id: int, body: WeightUpdate):
    """기존 기록의 몸무게 값을 수정한다."""
    if not (body.weight > 0):
        raise HTTPException(400, "올바른 몸무게가 아닙니다.")
    row = db.update_weight(measurement_id, body.weight)
    if row is None:
        raise HTTPException(404, "해당 기록이 없습니다.")
    return row


@app.delete("/api/measurements/{measurement_id}")
async def remove_measurement(measurement_id: int):
    if not db.delete_measurement(measurement_id):
        raise HTTPException(404, "해당 기록이 없습니다.")
    return {"ok": True}


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


# 브라우저/OS가 루트 경로로 요청하는 아이콘·매니페스트 파일 서빙.
# (화이트리스트 방식이라 임의 경로 노출 위험 없음)
_STATIC_ASSETS = {
    "favicon.ico",
    "favicon-16x16.png",
    "favicon-32x32.png",
    "apple-touch-icon.png",
    "android-chrome-192x192.png",
    "android-chrome-512x512.png",
    "site.webmanifest",
}


@app.get("/{filename}")
async def static_asset(filename: str):
    if filename not in _STATIC_ASSETS:
        raise HTTPException(404, "찾을 수 없습니다.")
    return FileResponse(STATIC_DIR / filename)
