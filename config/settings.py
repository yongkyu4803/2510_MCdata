"""
프로젝트 설정 파일
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if not exist
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# API Configuration
MUSICOW_API_URL = "https://data.musicow.com/files/v1/market/orders.json"
API_TIMEOUT = 30  # seconds
API_RETRY_COUNT = 3
API_RETRY_DELAY = 5  # seconds

# Data Collection
COLLECTION_INTERVAL_MINUTES = 5  # 데이터 수집 주기 (분)
DAILY_REPORT_TIME = "18:00"  # 일일 리포트 생성 시간

# Metrics Configuration
PREMIUM_THRESHOLD_HIGH = 10.0  # 고평가 기준 (%)
PREMIUM_THRESHOLD_LOW = -10.0  # 저평가 기준 (%)
LIQUIDITY_HIGH_SCORE = 80  # 유동성 높음 기준
LIQUIDITY_LOW_SCORE = 30  # 유동성 낮음 기준
REFERENCE_PRICE = 10000  # 정규화 수익률 계산 기준가

# Alert Configuration
ALERT_PREMIUM_THRESHOLD = 3.0  # 괴리율 알림 기준 (%)
ALERT_YIELD_CHANGE = 2.0  # 수익률 변동 알림 기준 (%)
ALERT_TIME_WINDOW = 10  # 변동 감지 시간 윈도우 (분)

# Report Configuration
REPORT_TOP_N = 3  # 리포트에 표시할 상위 N개
TSV_DELIMITER = '\t'  # TSV 구분자
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
FILE_DATE_FORMAT = "%Y%m%d_%H%M"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_FILE_BACKUP_COUNT = 5

# Optional: Webhook Configuration
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")