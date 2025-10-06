"""
뮤직카우 API 클라이언트
"""
import time
from typing import List, Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from config.settings import (
    MUSICOW_API_URL,
    API_TIMEOUT,
    API_RETRY_COUNT,
    API_RETRY_DELAY
)
from src.utils.logger import setup_logger
from src.utils.validators import DataValidator


class MusicowAPIClient:
    """뮤직카우 API 클라이언트"""

    def __init__(self):
        """초기화"""
        self.api_url = MUSICOW_API_URL
        self.logger = setup_logger(__name__, "api_client.log")
        self.validator = DataValidator()

        # 세션 설정 with 재시도 전략
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """
        재시도 전략이 포함된 세션 생성

        Returns:
            설정된 requests 세션
        """
        session = requests.Session()

        # 재시도 전략 설정
        retry_strategy = Retry(
            total=API_RETRY_COUNT,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            backoff_factor=1
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 헤더 설정
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        return session

    def fetch_orders(self) -> Optional[List[Dict[str, Any]]]:
        """
        주문 데이터 가져오기

        Returns:
            주문 데이터 리스트 또는 None
        """
        try:
            self.logger.info(f"API 호출 시작: {self.api_url}")

            response = self.session.get(
                self.api_url,
                timeout=API_TIMEOUT
            )

            # 상태 코드 확인
            response.raise_for_status()

            # JSON 파싱
            data = response.json()

            if not isinstance(data, list):
                self.logger.error(f"예상치 못한 응답 형식: {type(data)}")
                return None

            self.logger.info(f"API 호출 성공: {len(data)}개 주문 데이터 수신")
            return data

        except requests.exceptions.Timeout:
            self.logger.error(f"API 타임아웃: {API_TIMEOUT}초")
            return None

        except requests.exceptions.ConnectionError:
            self.logger.error("API 연결 실패")
            return None

        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP 에러: {e}")
            return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"요청 에러: {e}")
            return None

        except Exception as e:
            self.logger.error(f"예상치 못한 에러: {e}")
            return None

    def fetch_orders_with_retry(self) -> Optional[List[Dict[str, Any]]]:
        """
        재시도 로직이 포함된 주문 데이터 가져오기

        Returns:
            주문 데이터 리스트 또는 None
        """
        for attempt in range(API_RETRY_COUNT):
            self.logger.info(f"API 호출 시도 {attempt + 1}/{API_RETRY_COUNT}")

            data = self.fetch_orders()
            if data is not None:
                return data

            if attempt < API_RETRY_COUNT - 1:
                self.logger.info(f"{API_RETRY_DELAY}초 후 재시도...")
                time.sleep(API_RETRY_DELAY)

        self.logger.error(f"API 호출 실패: {API_RETRY_COUNT}번 시도 후 포기")
        return None

    def validate_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        주문 데이터 검증 및 필터링

        Args:
            orders: 원본 주문 데이터

        Returns:
            검증된 주문 데이터
        """
        validated_orders = []
        invalid_count = 0

        for order in orders:
            is_valid, errors = self.validator.validate_order(order)

            if is_valid:
                validated_orders.append(order)
            else:
                invalid_count += 1
                if invalid_count <= 3:  # 처음 3개만 로깅
                    self.logger.warning(f"유효하지 않은 주문: {errors}")

        if invalid_count > 0:
            self.logger.warning(f"총 {invalid_count}개의 유효하지 않은 주문 제외")

        self.logger.info(f"검증 완료: {len(validated_orders)}/{len(orders)} 유효")
        return validated_orders

    def get_validated_orders(self) -> Optional[List[Dict[str, Any]]]:
        """
        검증된 주문 데이터 가져오기 (메인 메소드)

        Returns:
            검증된 주문 데이터 리스트 또는 None
        """
        # API 호출
        orders = self.fetch_orders_with_retry()
        if orders is None:
            return None

        # 데이터 검증
        validated_orders = self.validate_orders(orders)

        if not validated_orders:
            self.logger.warning("유효한 주문 데이터가 없습니다")
            return None

        return validated_orders

    def test_connection(self) -> bool:
        """
        API 연결 테스트

        Returns:
            연결 성공 여부
        """
        try:
            self.logger.info("API 연결 테스트 시작")
            response = self.session.get(self.api_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.logger.info(f"API 연결 테스트 성공: {len(data)}개 데이터 확인")
                    return True

            self.logger.error(f"API 연결 테스트 실패: 상태코드 {response.status_code}")
            return False

        except Exception as e:
            self.logger.error(f"API 연결 테스트 실패: {e}")
            return False

    def close(self):
        """세션 종료"""
        self.session.close()
        self.logger.info("API 클라이언트 세션 종료")