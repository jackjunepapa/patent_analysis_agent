"""pytest: backend 디렉터리 기준으로 경로·클라이언트 설정."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parent.parent

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.chdir(BACKEND_ROOT)

# api 로드 전에 루트 .env 반영 (통합 테스트 OPENAI 키 인식)
try:
    from dotenv import load_dotenv

    load_dotenv(BACKEND_ROOT.parent / ".env")
except ImportError:
    pass


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from api import app

    return TestClient(app)