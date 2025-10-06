"""
공통 헬퍼 함수
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def save_json(data: Any, filepath: Path, indent: int = 2) -> bool:
    """
    JSON 파일 저장

    Args:
        data: 저장할 데이터
        filepath: 파일 경로
        indent: 들여쓰기 크기

    Returns:
        저장 성공 여부
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        print(f"JSON 저장 실패: {e}")
        return False


def load_json(filepath: Path) -> Optional[Any]:
    """
    JSON 파일 로드

    Args:
        filepath: 파일 경로

    Returns:
        로드된 데이터 또는 None
    """
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"JSON 로드 실패: {e}")
    return None


def get_timestamp(format_string: str = "%Y%m%d_%H%M%S") -> str:
    """
    현재 타임스탬프 반환

    Args:
        format_string: 날짜 형식 문자열

    Returns:
        형식화된 타임스탬프
    """
    return datetime.now().strftime(format_string)


def calculate_percentage(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    안전한 백분율 계산

    Args:
        numerator: 분자
        denominator: 분모
        default: 0 나누기 시 기본값

    Returns:
        백분율 값
    """
    if denominator == 0:
        return default
    return (numerator / denominator) * 100


def format_number(value: float, decimals: int = 2) -> str:
    """
    숫자 포맷팅

    Args:
        value: 포맷할 값
        decimals: 소수점 자리수

    Returns:
        포맷된 문자열
    """
    if decimals == 0:
        return f"{value:,.0f}"
    else:
        return f"{value:,.{decimals}f}"


def safe_get(data: Dict, key: str, default: Any = None) -> Any:
    """
    딕셔너리에서 안전하게 값 가져오기

    Args:
        data: 딕셔너리
        key: 키
        default: 기본값

    Returns:
        값 또는 기본값
    """
    return data.get(key, default)


def remove_duplicates(items: List[Dict], key: str = "order_no") -> List[Dict]:
    """
    리스트에서 중복 제거

    Args:
        items: 아이템 리스트
        key: 중복 체크 키

    Returns:
        중복 제거된 리스트
    """
    seen = set()
    result = []
    for item in items:
        if item.get(key) not in seen:
            seen.add(item.get(key))
            result.append(item)
    return result


def parse_datetime(date_string: str, format: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    날짜 문자열 파싱

    Args:
        date_string: 날짜 문자열
        format: 날짜 형식

    Returns:
        datetime 객체 또는 None
    """
    try:
        return datetime.strptime(date_string, format)
    except (ValueError, TypeError):
        return None