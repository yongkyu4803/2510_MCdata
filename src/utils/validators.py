"""
데이터 검증 유틸리티
"""
from typing import Dict, List, Any, Optional
from datetime import datetime


class DataValidator:
    """데이터 검증 클래스"""

    # 필수 필드 정의
    REQUIRED_FIELDS = [
        "order_no",
        "song_name",
        "song_artist",
        "song_category",
        "order_type",
        "order_price",
        "order_count",
        "order_status",
        "order_royalty_rate",
        "order_date",
        "recent_price"
    ]

    # 필드별 타입 정의
    FIELD_TYPES = {
        "order_no": str,
        "song_name": str,
        "song_artist": str,
        "song_category": str,
        "order_type": str,
        "order_price": (int, float),
        "order_count": (int, float),
        "leaves_count": (int, float),
        "order_status": str,
        "order_royalty_rate": (int, float),
        "order_date": str,
        "recent_price": (int, float),
        "url_link": str
    }

    # 유효한 값 정의
    VALID_ORDER_TYPES = ["구매", "판매"]
    VALID_ORDER_STATUS = ["대기", "완료", "취소", "체결"]  # "체결" 추가
    VALID_CATEGORIES = ["저작재산권", "저작인접권"]

    @classmethod
    def validate_order(cls, order: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        주문 데이터 검증

        Args:
            order: 검증할 주문 데이터

        Returns:
            (검증 성공 여부, 에러 메시지 리스트)
        """
        errors = []

        # 필수 필드 확인
        for field in cls.REQUIRED_FIELDS:
            if field not in order or order[field] is None:
                errors.append(f"필수 필드 누락: {field}")

        # 타입 검증
        for field, value in order.items():
            if field in cls.FIELD_TYPES and value is not None:
                expected_type = cls.FIELD_TYPES[field]
                if not isinstance(value, expected_type):
                    errors.append(f"타입 오류 - {field}: {type(value).__name__} (예상: {expected_type})")

        # 값 범위 검증
        if "order_price" in order and order["order_price"] is not None:
            if order["order_price"] <= 0:
                errors.append(f"가격이 0 이하: {order['order_price']}")

        if "order_royalty_rate" in order and order["order_royalty_rate"] is not None:
            if order["order_royalty_rate"] < 0:
                errors.append(f"수익률이 음수: {order['order_royalty_rate']}")

        # 유효한 값 검증
        if "order_type" in order and order["order_type"] not in cls.VALID_ORDER_TYPES:
            errors.append(f"잘못된 주문 타입: {order['order_type']}")

        if "order_status" in order and order["order_status"] not in cls.VALID_ORDER_STATUS:
            errors.append(f"잘못된 주문 상태: {order['order_status']}")

        # 날짜 형식 검증
        if "order_date" in order and order["order_date"]:
            try:
                datetime.strptime(order["order_date"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                errors.append(f"잘못된 날짜 형식: {order['order_date']}")

        return (len(errors) == 0, errors)

    @classmethod
    def validate_batch(cls, orders: List[Dict[str, Any]]) -> tuple[int, int, List[str]]:
        """
        배치 데이터 검증

        Args:
            orders: 주문 데이터 리스트

        Returns:
            (전체 개수, 유효한 개수, 전체 에러 메시지)
        """
        total_count = len(orders)
        valid_count = 0
        all_errors = []

        for i, order in enumerate(orders):
            is_valid, errors = cls.validate_order(order)
            if is_valid:
                valid_count += 1
            else:
                all_errors.extend([f"Order #{i+1}: {e}" for e in errors])

        return total_count, valid_count, all_errors