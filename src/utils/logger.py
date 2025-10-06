"""
로깅 유틸리티
"""
import logging
import logging.handlers
from pathlib import Path
from config.settings import (
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_FILE_MAX_SIZE,
    LOG_FILE_BACKUP_COUNT,
    LOGS_DIR
)


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    로거 설정 함수

    Args:
        name: 로거 이름
        log_file: 로그 파일명 (선택사항)

    Returns:
        설정된 로거 객체
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # 이미 핸들러가 있으면 중복 추가 방지
    if logger.handlers:
        return logger

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    console_formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (선택사항)
    if log_file:
        log_path = LOGS_DIR / log_file
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=LOG_FILE_MAX_SIZE,
            backupCount=LOG_FILE_BACKUP_COUNT
        )
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)

    return logger


# 기본 로거
main_logger = setup_logger("musicow_insight", "musicow_insight.log")