"""
🎤 간단한 실시간 PCM → Google Speech v2 STT 서버

요구사항:
- 브라우저 마이크 → 16kHz Int16 PCM → WebSocket → Google Speech v2
- interim/final 결과를 실시간으로 클라이언트에 전송
- 복잡한 FFmpeg/WebM 변환 없음, 오직 PCM만 사용

실행 방법:
1. 인증 설정: 
   - credentials/stt-credentials.json 파일 필요
   - 또는 GOOGLE_APPLICATION_CREDENTIALS 환경변수 설정
2. 실행: python app.py
3. 브라우저: http://localhost:8003/demo
"""

import asyncio
import base64
import json
import os
import socket
import time
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from google.cloud import speech_v2
from google.cloud.speech_v2 import SpeechAsyncClient
from google.oauth2 import service_account


# gRPC DNS 설정 (503 DNS 오류 해결)
# macOS/사내망에서 SRV 조회 실패가 흔함 - 아래 설정으로 우회
# 대안: 네트워크 변경/공용 DNS(8.8.8.8, 1.1.1.1)/프록시 설정 확인
os.environ.setdefault("GRPC_DNS_ENABLE_SRV_QUERY", "0")  # SRV 쿼리 비활성화
os.environ.setdefault("GRPC_DNS_RESOLVER", "native")     # 네이티브 DNS 리졸버 사용
os.environ.setdefault("GRPC_ENABLE_FORK_SUPPORT", "1")   # Fork 지원 활성화
os.environ.setdefault("GRPC_POLL_STRATEGY", "poll")      # 안정적인 폴링 전략

# 설정
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "stttest-471811")
CREDENTIALS_PATH = "credentials/stt-credentials.json"

app = FastAPI(title="🎤 간단한 PCM STT 서버")

def dns_warmup(host: str = "speech.googleapis.com", port: int = 443, retries: int = 5) -> bool:
    """
    DNS 예열 및 연결성 확인
    macOS/사내망에서 DNS 해결 실패가 흔함 - 여러 방법으로 시도
    """
    
    # 1. 기본 DNS 해결 시도
    for attempt in range(retries):
        try:
            print(f"🌐 DNS 예열 시도 {attempt + 1}/{retries}: {host}:{port}")
            result = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            print(f"✅ DNS 예열 성공: {len(result)}개 주소 해결됨")
            
            # 첫 번째 주소로 실제 연결 테스트
            first_addr = result[0]
            test_socket = socket.socket(first_addr[0], first_addr[1])
            test_socket.settimeout(5.0)
            test_socket.connect(first_addr[4])
            test_socket.close()
            print("✅ 실제 연결 테스트 성공")
            return True
            
        except socket.gaierror as e:
            print(f"❌ DNS 해결 실패 ({attempt + 1}/{retries}): {e}")
        except (ConnectionRefusedError, OSError, socket.timeout) as e:
            print(f"⚠️ 연결 테스트 실패하지만 DNS는 성공 ({attempt + 1}/{retries}): {e}")
            return True  # DNS는 성공했으므로 OK
        except Exception as e:
            print(f"❌ DNS 예열 실패 ({attempt + 1}/{retries}): {e}")
            
        if attempt < retries - 1:
            wait_time = 2.0 ** attempt  # 지수 백오프: 1s, 2s, 4s, 8s
            print(f"⏳ {wait_time:.1f}초 후 재시도...")
            time.sleep(wait_time)
    
    # 2. 대체 DNS 서버로 시도
    print("🔄 공용 DNS 서버로 대체 시도...")
    try:
        import subprocess
        result = subprocess.run(['nslookup', host, '8.8.8.8'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and 'Address:' in result.stdout:
            print("✅ 공용 DNS(8.8.8.8)로 해결 성공")
            return True
    except Exception as e:
        print(f"❌ 공용 DNS 시도 실패: {e}")
    
    print(f"💀 DNS 예열 최종 실패: {host}:{port}")
    print("💡 해결 방법:")
    print("   1. 네트워크 연결 확인")
    print("   2. DNS 설정을 8.8.8.8 또는 1.1.1.1로 변경")
    print("   3. VPN/프록시 설정 확인")
    print("   4. 방화벽 설정 확인")
    return False

async def create_async_speech_client_with_retry(credentials_path: str, retries: int = 3) -> Optional[SpeechAsyncClient]:
    """
    재시도 로직이 포함된 SpeechAsyncClient 생성
    DNS 해결 실패 시에도 우회 방법 시도
    """
    
    # 1. DNS 예열 (실패해도 계속 진행)
    dns_ok = dns_warmup()
    if not dns_ok:
        print("⚠️ DNS 예열 실패했지만 클라이언트 생성 계속 시도...")
    
    # 2. 인증 정보 로드
    cred_path = Path(credentials_path)
    if not cred_path.exists():
        print(f"⚠️ 인증 파일을 찾을 수 없습니다: {credentials_path}")
        print("💡 GOOGLE_APPLICATION_CREDENTIALS 환경변수 사용 시도...")
        credentials = None
    else:
        credentials = service_account.Credentials.from_service_account_file(str(cred_path))
    
    # 3. 클라이언트 생성 재시도 (다양한 설정으로)
    for attempt in range(retries):
        try:
            print(f"🔧 SpeechAsyncClient 생성 시도 {attempt + 1}/{retries}")
            
            # 시도 1: 일반 클라이언트
            if attempt == 0:
                if credentials:
                    client = SpeechAsyncClient(credentials=credentials)
                else:
                    client = SpeechAsyncClient()  # ADC 사용
                    
            # 시도 2: 커스텀 엔드포인트
            elif attempt == 1:
                from google.api_core import client_options
                opts = client_options.ClientOptions(
                    api_endpoint="speech.googleapis.com:443"
                )
                if credentials:
                    client = SpeechAsyncClient(credentials=credentials, client_options=opts)
                else:
                    client = SpeechAsyncClient(client_options=opts)
                    
            # 시도 3: 다른 엔드포인트
            else:
                from google.api_core import client_options
                opts = client_options.ClientOptions(
                    api_endpoint="speech.googleapis.com"
                )
                if credentials:
                    client = SpeechAsyncClient(credentials=credentials, client_options=opts)
                else:
                    client = SpeechAsyncClient(client_options=opts)
            
            print(f"✅ SpeechAsyncClient 생성 성공 (시도: {attempt + 1})")
            return client
            
        except Exception as e:
            print(f"❌ SpeechAsyncClient 생성 실패 ({attempt + 1}/{retries}): {e}")
            if "DNS" in str(e) or "resolution" in str(e):
                print("🔍 DNS 관련 오류 감지 - 네트워크 설정 확인 필요")
            
            if attempt < retries - 1:
                wait_time = 3.0 * (attempt + 1)  # 3s, 6s, 9s
                print(f"⏳ {wait_time}초 후 재시도...")
                await asyncio.sleep(wait_time)
    
    print("💀 SpeechAsyncClient 생성 최종 실패")
    print("💡 문제 해결 방법:")
    print("   1. 인터넷 연결 상태 확인")
    print("   2. 방화벽/보안 소프트웨어 확인")  
    print("   3. DNS 설정을 8.8.8.8 또는 1.1.1.1로 변경")
    print("   4. VPN 연결 시 VPN 해제 후 재시도")
    print("   5. Google Cloud 인증 설정 확인")
    return None



@app.get("/demo")
async def demo_page():
    """데모 클라이언트 페이지"""
    return FileResponse("templates/demo_client.html")

async def request_generator(recognizer: str, streaming_config, pcm_queue: asyncio.Queue):
    """
    Google Speech v2 스트리밍 요청 제너레이터 - 단순화 버전
    """
    try:
        # 1. 첫 번째 요청: 설정만 전송
        print("📡 STT 설정 전송")
        yield speech_v2.StreamingRecognizeRequest(
            recognizer=recognizer,
            streaming_config=streaming_config
        )
        
        # 2. 첫 번째 PCM 데이터 대기 (중요!)
        print("⏳ 첫 번째 PCM 데이터 대기 중...")
        first_pcm = await pcm_queue.get()
        
        if first_pcm is None:
            print("🔚 첫 PCM 수신 전 종료")
            return
        
        print(f"✅ 첫 PCM 수신: {len(first_pcm)} bytes")
        yield speech_v2.StreamingRecognizeRequest(audio=first_pcm)
        
        # 3. 이후 PCM 청크들 연속 처리
        chunk_count = 1
        while True:
            try:
                # 타임아웃으로 큐에서 데이터 수신 (무한 대기 방지)
                pcm_data = await asyncio.wait_for(pcm_queue.get(), timeout=30.0)
                
                # 종료 신호
                if pcm_data is None:
                    print("🔚 PCM 스트림 종료 신호 수신")
                    break
                
                chunk_count += 1
                
                # 너무 큰 청크는 분할
                if len(pcm_data) > 20000:  # 20KB로 제한
                    print(f"✂️ 큰 청크 분할: {len(pcm_data)} bytes")
                    pcm_data = pcm_data[:20000]
                
                print(f"🎵 PCM 청크 [{chunk_count}]: {len(pcm_data)} bytes")
                yield speech_v2.StreamingRecognizeRequest(audio=pcm_data)
                
            except asyncio.TimeoutError:
                print("⏰ PCM 데이터 수신 타임아웃")
                break
                
    except Exception as e:
        print(f"❌ 요청 제너레이터 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🔚 요청 제너레이터 종료")

@app.websocket("/ws/stt")
async def websocket_stt(websocket: WebSocket):
    """WebSocket STT 엔드포인트"""
    await websocket.accept()
    print("🔌 WebSocket 연결됨")
    
    # 재시도 로직이 포함된 클라이언트 생성
    client = await create_async_speech_client_with_retry(CREDENTIALS_PATH)
    if not client:
        await websocket.send_json({
            "type": "error", 
            "message": "Google Speech 클라이언트 초기화 실패 - 네트워크/DNS 이슈 또는 인증 설정을 확인하세요"
        })
        await websocket.close()
        return
    
    # PCM 데이터 큐
    pcm_queue = asyncio.Queue()
    
    # Google Speech v2 설정
    recognizer = f"projects/{PROJECT_ID}/locations/global/recognizers/_"
    
    config = speech_v2.RecognitionConfig(
        explicit_decoding_config=speech_v2.ExplicitDecodingConfig(
            encoding=speech_v2.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            audio_channel_count=1
        ),
        language_codes=["ko-KR"],
        model="latest_long",
        features=speech_v2.RecognitionFeatures(
            enable_automatic_punctuation=True,
            enable_word_confidence=True,
            max_alternatives=1
        )
    )
    
    streaming_config = speech_v2.StreamingRecognitionConfig(
        config=config,
        streaming_features=speech_v2.StreamingRecognitionFeatures(
            interim_results=True
        )
    )
    
    is_connected = True
    
    async def stt_processor():
        """STT 처리 코루틴 - 비동기 클라이언트 사용"""
        try:
            print(f"🎤 Google Speech v2 비동기 스트리밍 시작: {recognizer}")
            
            # 요청 제너레이터 생성
            requests = request_generator(recognizer, streaming_config, pcm_queue)
            
            # 🔥 핵심: 비동기 스트리밍 인식
            responses = await client.streaming_recognize(requests=requests)
            
            response_count = 0
            
            # 🔥 핵심: async for로 응답 처리
            async for response in responses:
                response_count += 1
                
                if not is_connected:
                    print("🔌 연결 종료됨 - STT 처리 중단")
                    break
                
                if not response.results:
                    continue
                
                result = response.results[0]
                if not result.alternatives:
                    continue
                
                alternative = result.alternatives[0]
                transcript = (alternative.transcript or "").strip()
                confidence = getattr(alternative, 'confidence', 0.0)
                
                if not transcript:
                    continue
                
                # 결과 타입 결정
                result_type = "final" if result.is_final else "interim"
                
                print(f"📝 [{result_type}] {transcript} (신뢰도: {confidence:.2f})")
                
                # 클라이언트에 전송
                if is_connected:
                    try:
                        payload = {
                            "type": result_type,
                            "text": transcript,
                            "confidence": confidence,
                            "is_final": bool(result.is_final)
                        }
                        await websocket.send_json(payload)
                    except Exception as send_error:
                        print(f"❌ 결과 전송 실패: {send_error}")
                        break
                        
        except Exception as e:
            print(f"❌ STT 처리 오류: {e}")
            import traceback
            traceback.print_exc()
            if is_connected:
                try:
                    await websocket.send_json({
                        "type": "error", 
                        "message": f"STT 처리 오류: {str(e)}"
                    })
                except:
                    pass
        finally:
            print("🔚 STT 처리 코루틴 종료")
    
    # STT 처리 태스크 시작
    stt_task = asyncio.create_task(stt_processor())
    
    try:
        # WebSocket 메시지 처리 루프
        while is_connected:
            try:
                # 메시지 수신
                message = await websocket.receive_text()
                data = json.loads(message)
                msg_type = data.get("type", "unknown")
                
                if msg_type == "start_recording":
                    print("🎙️ 녹음 시작")
                    await websocket.send_json({"type": "status", "message": "녹음 시작됨"})
                    
                elif msg_type == "audio_pcm":
                    # PCM 데이터 수신 및 처리
                    audio_b64 = data.get("audio", "")
                    if audio_b64:
                        try:
                            pcm_bytes = base64.b64decode(audio_b64)
                            print(f"🔊 PCM 수신: {len(pcm_bytes)} bytes")
                            await pcm_queue.put(pcm_bytes)
                        except Exception as decode_error:
                            print(f"❌ PCM 디코딩 실패: {decode_error}")
                    
                elif msg_type == "stop_recording":
                    print("⏹️ 녹음 중지")
                    # 종료 신호 전송
                    await pcm_queue.put(None)
                    await websocket.send_json({"type": "status", "message": "녹음 중지됨"})
                    break
                    
                else:
                    print(f"❓ 알 수 없는 메시지 타입: {msg_type}")
                    
            except json.JSONDecodeError:
                print("❌ JSON 파싱 오류")
            except Exception as msg_error:
                print(f"❌ 메시지 처리 오류: {msg_error}")
                break
                
    except WebSocketDisconnect:
        print("🔌 WebSocket 연결 해제")
    except Exception as e:
        print(f"❌ WebSocket 오류: {e}")
    finally:
        is_connected = False
        
        # STT 처리 태스크 정리
        if not stt_task.done():
            stt_task.cancel()
            try:
                await stt_task
            except asyncio.CancelledError:
                pass
        
        # 큐 정리
        try:
            await pcm_queue.put(None)
        except:
            pass
        
        print("🧹 WebSocket 세션 정리 완료")

if __name__ == "__main__":
    print("🎯 간단한 실시간 PCM STT 시스템")
    print("=" * 50)
    print(f"📋 설정:")
    print(f"   - 프로젝트: {PROJECT_ID}")
    print(f"   - 인증파일: {CREDENTIALS_PATH}")
    print(f"   - 언어: ko-KR")
    print(f"   - 모델: latest_long")
    print("=" * 50)
    print(f"🔧 gRPC DNS 설정 (DNS 해결 문제 방지):")
    print(f"   - GRPC_DNS_ENABLE_SRV_QUERY: {os.environ.get('GRPC_DNS_ENABLE_SRV_QUERY', 'not set')}")
    print(f"   - GRPC_DNS_RESOLVER: {os.environ.get('GRPC_DNS_RESOLVER', 'not set')}")
    print(f"   - GRPC_ENABLE_FORK_SUPPORT: {os.environ.get('GRPC_ENABLE_FORK_SUPPORT', 'not set')}")
    print(f"   - GRPC_POLL_STRATEGY: {os.environ.get('GRPC_POLL_STRATEGY', 'not set')}")
    print("=" * 50)
    print("🚀 서버 시작 중...")
    print("📱 브라우저에서 http://localhost:8003/demo 접속하세요")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8003,
        reload=False,  # 단순함을 위해 리로드 비활성화
        log_level="info"
    )