# 🎤 실시간 PCM → Google Speech v2 STT 시스템

브라우저 마이크에서 16kHz PCM 오디오를 실시간으로 Google Speech-to-Text v2 API로 전송하여 한국어 음성인식을 수행하는 간단하고 안정적인 시스템입니다.

## 🚀 빠른 시작

### 1. 자동 설치 및 실행
```bash
chmod +x setup.sh
./setup.sh
```

### 2. 수동 설치
```bash
# Python 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate    # Windows

# 의존성 설치
pip install -r requirements.txt

# Google Cloud 인증 설정 (아래 인증 설정 섹션 참조)
# credentials/stt-credentials.json 파일 배치

# 서버 실행
python app.py
```

### 3. 브라우저 접속
- http://localhost:8003/demo 접속
- 🎙️ **Start Recording** 버튼 클릭
- 마이크 권한 허용 후 한국어로 말하기
- 실시간 interim/final 결과 확인
- ⏹️ **Stop Recording**으로 종료

## 📋 시스템 요구사항

- **Python**: 3.8 이상
- **OS**: macOS, Linux, Windows
- **브라우저**: Chrome, Firefox, Safari (WebRTC 지원)
- **네트워크**: 인터넷 연결 필수 (Google Cloud API 호출)

## 🔑 Google Cloud 인증 설정

### 방법 1: 서비스 계정 키 파일 (권장)
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 생성 또는 선택
3. Cloud Speech-to-Text API 활성화
4. 서비스 계정 생성 및 키 다운로드 (JSON 형식)
5. 다운로드한 파일을 `credentials/stt-credentials.json`으로 저장

### 방법 2: 환경변수 설정
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/credentials.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

## 🛠️ 기술 스펙

### 오디오 처리
- **샘플레이트**: 16kHz
- **채널**: Mono (1채널)  
- **포맷**: Int16 PCM
- **청크 크기**: 100ms (3200 bytes)
- **전송**: Base64 인코딩 → WebSocket

### API 설정
- **Google Speech v2**: 비동기 스트리밍 인식
- **언어**: ko-KR (한국어)
- **모델**: latest_long
- **기능**: interim_results, 자동 구두점, 단어 신뢰도

### 네트워크 안정성
- gRPC DNS SRV 쿼리 비활성화 (macOS/사내망 호환성)
- 재시도 로직 (DNS 해결, 클라이언트 생성)
- 연결 실패 시 다양한 우회 방법 시도

## 📁 파일 구조

```
StreamingShare/
├── README.md              # 이 파일
├── requirements.txt       # Python 의존성
├── setup.sh              # 자동 설치 스크립트
├── app.py                 # FastAPI 서버
├── templates/
│   └── demo_client.html   # 웹 클라이언트
└── credentials/
    └── stt-credentials.json  # Google Cloud 인증 (사용자 추가)
```