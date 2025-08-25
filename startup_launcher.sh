LOG_FILE="/var/log/braille_system.log"
PROJECT_DIR="/home/junekim617/project1"

# 로그 함수
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 정리 함수
cleanup() {
    log_message "시스템 종료 신호를 받았습니다. 프로세스들을 종료합니다..."
    
    if [ ! -z "$PID1" ]; then
        kill $PID1 2>/dev/null
        log_message "STT 서비스 (PID: $PID1) 종료됨"
    fi
    
    if [ ! -z "$PID2" ]; then
        kill $PID2 2>/dev/null
        log_message "점자 리더 서비스 (PID: $PID2) 종료됨"
    fi
    
    exit 0
}

# 신호 트랩 설정
trap cleanup SIGTERM SIGINT

log_message "🚀 Braille System 시작..."

# 프로젝트 디렉토리로 이동
cd "$PROJECT_DIR" || {
    log_message "❌ 프로젝트 디렉토리로 이동 실패: $PROJECT_DIR"
    exit 1
}

# 오디오 시스템이 준비될 때까지 대기
log_message "🎵 오디오 시스템 준비 대기 중..."
sleep 10

# 첫 번째 프로그램 시작 (가상환경에서 STT)
log_message "🎤 STT 서비스 시작 중..."
source venv/bin/activate
python3 vtb.py >> "$LOG_FILE" 2>&1 &
PID1=$!
log_message "✅ STT 서비스 시작됨 (PID: $PID1)"

# 두 번째 프로그램 시작 전 잠시 대기
sleep 5

# 두 번째 프로그램 시작 (시스템 환경에서 점자 리더)
log_message "📟 점자 리더 서비스 시작 중..."
python3 command.py >> "$LOG_FILE" 2>&1 &
PID2=$!
log_message "✅ 점자 리더 서비스 시작됨 (PID: $PID2)"

log_message "🎯 모든 서비스가 시작되었습니다."
log_message "STT PID: $PID1, 점자 리더 PID: $PID2"

# 프로세스 감시 루프
while true; do
    # 첫 번째 프로세스 확인
    if ! kill -0 $PID1 2>/dev/null; then
        log_message "⚠️ STT 서비스가 종료되었습니다. 재시작합니다..."
        cd "$PROJECT_DIR"
        source venv/bin/activate
        python3 vtb.py >> "$LOG_FILE" 2>&1 &
        PID1=$!
        log_message "🔄 STT 서비스 재시작됨 (PID: $PID1)"
    fi
    
    # 두 번째 프로세스 확인
    if ! kill -0 $PID2 2>/dev/null; then
        log_message "⚠️ 점자 리더 서비스가 종료되었습니다. 재시작합니다..."
        cd "$PROJECT_DIR"
        python3 command.py >> "$LOG_FILE" 2>&1 &
        PID2=$!
        log_message "🔄 점자 리더 서비스 재시작됨 (PID: $PID2)"
    fi
    
    sleep 30  # 30초마다 확인
done
