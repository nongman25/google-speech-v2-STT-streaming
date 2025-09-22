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

## 🔧 문제 해결

### DNS 해결 실패
```
❌ DNS 예열 실패: [Errno 8] nodename nor servname provided, or not known
```
**해결 방법:**
1. 네트워크 연결 상태 확인
2. DNS 설정을 공용 DNS로 변경 (8.8.8.8, 1.1.1.1)
3. VPN 연결 시 VPN 해제 후 재시도
4. 방화벽/보안 소프트웨어 확인

### 인증 오류
```
❌ Google Speech 클라이언트 초기화 실패
```
**해결 방법:**
1. `credentials/stt-credentials.json` 파일 존재 확인
2. Google Cloud 프로젝트에서 Speech-to-Text API 활성화 확인
3. 서비스 계정 권한 확인 (Cloud Speech Client 역할)

### 마이크 접근 실패
**해결 방법:**
1. HTTPS 사용 (localhost는 HTTP 허용)
2. 브라우저 마이크 권한 설정 확인
3. 다른 브라우저로 시도

## 🎯 주요 기능

### ✅ 실시간 스트리밍
- 마이크 입력을 100ms 단위로 실시간 처리
- interim 결과를 0.2~0.5초 간격으로 표시
- final 결과를 문장 단위로 확정

### ✅ 안정적인 연결
- DNS 해결 실패 시 자동 우회
- 네트워크 오류 시 재시도 로직
- WebSocket 연결 안전성 보장

### ✅ 사용자 친화적
- 간단한 웹 인터페이스
- 실시간 로그 표시
- 시각적 피드백 (색상 구분)

## 📝 개발 정보

- **개발자**: GitHub Copilot + Assistant
- **라이선스**: MIT
- **버전**: 2.0
- **최종 업데이트**: 2025년 9월

## 🆘 지원

문제가 발생하면 다음 정보와 함께 이슈를 제출해주세요:

1. 운영체제 및 버전
2. Python 버전 (`python --version`)
3. 오류 메시지 전체
4. 네트워크 환경 (회사망, 가정용 등)

---

**🎤 즐거운 음성인식 경험을 위해!**