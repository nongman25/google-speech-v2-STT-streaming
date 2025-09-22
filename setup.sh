#!/bin/bash

# 🎤 실시간 PCM STT 시스템 - 자동 설치 및 실행 스크립트

set -e  # 오류 시 즉시 중단

echo "🎤 실시간 PCM → Google Speech v2 STT 시스템"
echo "==============================================="
echo "📅 버전: 2.0 (2025년 9월)"
echo "🔧 자동 설치를 시작합니다..."
echo ""

# 시스템 정보 확인
echo "🖥️  시스템 정보:"
echo "   - OS: $(uname -s)"
echo "   - 아키텍처: $(uname -m)"
echo "   - Python: $(python3 --version 2>/dev/null || echo 'Python 3 필요')"
echo ""

# Python 3 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3가 설치되지 않았습니다."
    echo "💡 Python 3.8 이상을 설치해주세요:"
    echo "   - macOS: brew install python3"
    echo "   - Ubuntu: sudo apt install python3 python3-pip python3-venv"
    echo "   - Windows: https://python.org 에서 다운로드"
    exit 1
fi

# pip 확인
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo "❌ pip가 설치되지 않았습니다."
    echo "💡 pip를 설치해주세요: python3 -m ensurepip --upgrade"
    exit 1
fi

echo "✅ Python 환경 확인 완료"

# 가상환경 생성
if [ ! -d ".venv" ]; then
    echo "📦 Python 가상환경 생성 중..."
    python3 -m venv .venv
    echo "✅ 가상환경 생성 완료"
else
    echo "📦 기존 가상환경 발견"
fi

# 가상환경 활성화
echo "🔌 가상환경 활성화 중..."
source .venv/bin/activate

# 의존성 설치
echo "📥 Python 패키지 설치 중..."
echo "   (시간이 좀 걸릴 수 있습니다...)"

pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo "✅ 패키지 설치 완료"

# 설치 확인
echo "🔍 설치 확인 중..."
if python -c "
import fastapi, uvicorn, websockets
from google.cloud import speech_v2
from google.cloud.speech_v2 import SpeechAsyncClient
print('✅ 모든 핵심 패키지 정상')
" 2>/dev/null; then
    echo "✅ 설치 검증 성공"
else
    echo "❌ 패키지 설치 검증 실패"
    echo "💡 수동으로 확인해주세요: pip list"
    exit 1
fi

# Google Cloud 인증 확인
echo ""
echo "🔑 Google Cloud 인증 확인 중..."
if [ -f "credentials/stt-credentials.json" ]; then
    echo "✅ 인증 파일 발견: credentials/stt-credentials.json"
    export GOOGLE_APPLICATION_CREDENTIALS="credentials/stt-credentials.json"
else
    echo "⚠️  Google Cloud 인증 파일이 없습니다."
    echo ""
    echo "📋 다음 단계를 완료해주세요:"
    echo "1. Google Cloud Console (https://console.cloud.google.com) 접속"
    echo "2. 프로젝트 생성 및 Cloud Speech-to-Text API 활성화"
    echo "3. 서비스 계정 생성 및 키 다운로드 (JSON)"
    echo "4. 다운로드한 파일을 credentials/stt-credentials.json으로 저장"
    echo ""
    echo "💡 임시로 환경변수로도 설정 가능합니다:"
    echo "   export GOOGLE_APPLICATION_CREDENTIALS='/path/to/your/key.json'"
    echo ""
    read -p "인증 설정을 완료했습니까? 계속 진행하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "📚 README.md를 참조하여 인증 설정을 완료한 후 다시 실행해주세요."
        exit 1
    fi
fi

# 네트워크 연결 확인
echo "🌐 네트워크 연결 확인 중..."
if ping -c 1 google.com > /dev/null 2>&1; then
    echo "✅ 인터넷 연결 정상"
else
    echo "⚠️  인터넷 연결을 확인해주세요."
fi

# 포트 확인
PORT=8003
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  포트 $PORT가 사용 중입니다."
    echo "💡 다른 프로세스를 종료하거나 app.py에서 포트를 변경해주세요."
fi

echo ""
echo "🎉 설치 및 설정 완료!"
echo "==============================================="
echo ""
echo "🚀 서버를 시작합니다..."
echo "📱 브라우저에서 http://localhost:$PORT/demo 에 접속하세요"
echo ""
echo "💡 사용법:"
echo "   1. 브라우저에서 페이지 열기"  
echo "   2. Start Recording 버튼 클릭"
echo "   3. 마이크 권한 허용"
echo "   4. 한국어로 말하기"
echo "   5. 실시간 결과 확인"
echo "   6. Stop Recording으로 종료"
echo ""
echo "🛑 서버 종료: Ctrl+C"
echo "==============================================="
echo ""

# 서버 실행
python app.py