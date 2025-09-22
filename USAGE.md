# 🎤 실시간 PCM → Google Speech v2 STT 키트 사용법

## ⚡ 빠른 시작 (자동 설치)

```bash
# StreamingShare 폴더로 이동
cd StreamingShare

# 자동 설치 및 실행
./setup.sh
```

**끝!** 브라우저에서 자동으로 http://localhost:8003/demo 가 열립니다.

---

## 📋 사전 준비사항

### 1. Google Cloud 인증 설정

1. **Google Cloud Console 접속**
   - https://console.cloud.google.com 방문
   - 프로젝트 생성 또는 기존 프로젝트 선택

2. **Cloud Speech-to-Text API 활성화**
   - API 및 서비스 → 라이브러리
   - "Cloud Speech-to-Text API" 검색 후 활성화

3. **서비스 계정 생성**
   - IAM 및 관리 → 서비스 계정
   - "서비스 계정 만들기" 클릭
   - 역할: "Cloud Speech 클라이언트" 또는 "편집자"

4. **인증 키 다운로드**
   - 생성된 서비스 계정 클릭
   - 키 탭 → 키 추가 → JSON
   - 다운로드한 파일을 `credentials/stt-credentials.json`로 저장

### 2. 시스템 요구사항

- **Python 3.8 이상**
- **인터넷 연결** (Google Cloud API 접근용)
- **현대적인 브라우저** (Chrome, Firefox, Safari, Edge)

---

## 🛠️ 수동 설치 (고급 사용자)

### 1. Python 가상환경 생성

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
```

### 2. 의존성 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. 서버 실행

```bash
python app.py
```

### 4. 브라우저 접속

http://localhost:8003/demo

---

## 🎯 사용 방법

1. **브라우저에서 페이지 접속**
   - http://localhost:8003/demo

2. **Start Recording 버튼 클릭**
   - 마이크 권한 허용

3. **한국어로 말하기**
   - 실시간으로 interim(임시) 결과 표시
   - 문장 완료 시 final(최종) 결과 확정

4. **Stop Recording으로 종료**

---

## 🔧 기술 사양

### 오디오 처리
- **입력**: 브라우저 마이크
- **샘플링**: 16kHz, 16-bit, 모노
- **포맷**: Int16 PCM → Base64 인코딩
- **전송**: WebSocket 실시간 스트리밍

### STT 엔진
- **플랫폼**: Google Cloud Speech-to-Text v2
- **언어**: 한국어 (ko-KR)
- **모델**: latest_long (최신 긴 형식 모델)
- **기능**: interim_results (실시간 중간 결과)

### 서버
- **프레임워크**: FastAPI + WebSocket
- **비동기**: async/await 패턴
- **DNS 최적화**: gRPC DNS 설정으로 연결 안정성 향상

---

## 🚨 문제 해결

### DNS 해결 오류

```
❌ DNS resolution failed for speech.googleapis.com
```

**해결 방법:**
1. DNS 설정을 8.8.8.8 또는 1.1.1.1로 변경
2. VPN 연결 시 VPN 해제 후 재시도
3. 방화벽/보안 소프트웨어 확인

### 마이크 접근 오류

```
❌ 마이크 액세스 실패
```

**해결 방법:**
1. 브라우저에서 마이크 권한 허용
2. HTTPS 환경에서 테스트 (필요시)
3. 다른 브라우저로 시도

### 인증 오류

```
❌ Google Speech 클라이언트 초기화 실패
```

**해결 방법:**
1. `credentials/stt-credentials.json` 파일 확인
2. Google Cloud 프로젝트 및 API 활성화 확인
3. 서비스 계정 권한 확인

### 포트 충돌

```
⚠️ 포트 8003가 사용 중입니다
```

**해결 방법:**
1. `app.py`에서 `port=8003`을 다른 포트로 변경
2. 또는 기존 프로세스 종료: `lsof -ti:8003 | xargs kill -9`

---

## 📁 파일 구조

```
StreamingShare/
├── README.md                    # 이 파일
├── app.py                       # FastAPI 서버
├── setup.sh                     # 자동 설치 스크립트
├── requirements.txt             # Python 의존성
├── credentials/
│   ├── stt-credentials.json     # Google Cloud 인증 (사용자 제공)
│   └── stt-credentials.json.template  # 인증 파일 템플릿
└── templates/
    └── demo_client.html         # 브라우저 클라이언트
```

---

## 🔄 개발 히스토리

- **v1.0**: 복잡한 FFmpeg 기반 구현
- **v2.0**: 단순한 PCM 전용 구현 ← **현재 버전**
  - DNS 해결 문제 해결
  - TypedArray PCM 변환 최적화
  - 비동기 Google Speech v2 클라이언트
  - 완전한 배포 키트 패키징

---

## 🆘 지원

문제가 발생하면 다음을 확인해주세요:

1. **네트워크 연결**: `ping google.com`
2. **Python 버전**: `python3 --version`
3. **의존성 설치**: `pip list`
4. **로그 확인**: 터미널에서 상세한 오류 메시지 확인

**추가 도움이 필요하면 GitHub Issues 또는 문서의 트러블슈팅 섹션을 참조하세요.**

---

**🎉 즐거운 실시간 STT 체험 되세요!**