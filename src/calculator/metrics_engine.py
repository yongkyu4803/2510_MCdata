"""
지표 계산 엔진
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

from config.settings import (
    PREMIUM_THRESHOLD_HIGH,
    PREMIUM_THRESHOLD_LOW,
    LIQUIDITY_HIGH_SCORE,
    LIQUIDITY_LOW_SCORE,
    REFERENCE_PRICE
)
from src.utils.logger import setup_logger
from src.utils.helpers import calculate_percentage, safe_get


class MetricsEngine:
    """지표 계산 엔진"""

    def __init__(self):
        """초기화"""
        self.logger = setup_logger(__name__, "metrics_engine.log")
        self.reference_price = REFERENCE_PRICE

    def calculate_spread_rate(self, order_price: float, recent_price: float) -> Optional[float]:
        """
        스프레드율 계산

        스프레드율 (%) = (order_price - recent_price) / recent_price × 100

        Args:
            order_price: 주문 가격
            recent_price: 최근 체결가

        Returns:
            스프레드율 (%) 또는 None
        """
        try:
            if recent_price == 0:
                return None

            spread_rate = ((order_price - recent_price) / recent_price) * 100
            return round(spread_rate, 2)

        except (TypeError, ZeroDivisionError):
            return None

    def calculate_expected_yield(
        self,
        order_royalty_rate: float,
        order_price: float,
        reference_price: Optional[float] = None
    ) -> Optional[float]:
        """
        예상 수익률 계산

        예상 수익률 (%) = (order_royalty_rate × 기준단가) / order_price × 100

        Args:
            order_royalty_rate: 1년 수익률 (0.08 = 8%)
            order_price: 주문 가격
            reference_price: 기준단가 (기본값: REFERENCE_PRICE)

        Returns:
            예상 수익률 (%) 또는 None
        """
        try:
            if order_price == 0:
                return None

            ref_price = reference_price or self.reference_price
            expected_yield = (order_royalty_rate * ref_price / order_price) * 100

            return round(expected_yield, 2)

        except (TypeError, ZeroDivisionError):
            return None

    def calculate_liquidity_score(
        self,
        orders: List[Dict[str, Any]],
        song_name: str
    ) -> float:
        """
        유동성 점수 계산 (0-100)

        다음 요소 기반:
        1. 호가 스프레드 (40%) - 매수/매도 가격 차이
        2. 주문 깊이 (30%) - 대기 중인 주문 수
        3. 갱신 빈도 (30%) - 최근 주문 빈도

        Args:
            orders: 전체 주문 데이터
            song_name: 곡 이름

        Returns:
            유동성 점수 (0-100)
        """
        try:
            # 해당 곡의 주문만 필터링
            song_orders = [o for o in orders if o.get("song_name") == song_name]

            if not song_orders:
                return 0.0

            # 1. 호가 스프레드 점수 (40%)
            spread_score = self._calculate_spread_score(song_orders)

            # 2. 주문 깊이 점수 (30%)
            depth_score = self._calculate_depth_score(song_orders)

            # 3. 갱신 빈도 점수 (30%)
            frequency_score = self._calculate_frequency_score(song_orders)

            # 가중 평균
            total_score = (
                spread_score * 0.4 +
                depth_score * 0.3 +
                frequency_score * 0.3
            )

            return round(total_score, 1)

        except Exception as e:
            self.logger.warning(f"유동성 점수 계산 실패 ({song_name}): {e}")
            return 0.0

    def _calculate_spread_score(self, song_orders: List[Dict[str, Any]]) -> float:
        """
        호가 스프레드 점수 계산

        스프레드가 작을수록 높은 점수

        Args:
            song_orders: 특정 곡의 주문 데이터

        Returns:
            스프레드 점수 (0-100)
        """
        try:
            # 대기 중인 매수/매도 주문 필터링
            buy_orders = [
                o for o in song_orders
                if o.get("order_type") == "구매" and o.get("order_status") == "대기"
            ]
            sell_orders = [
                o for o in song_orders
                if o.get("order_type") == "판매" and o.get("order_status") == "대기"
            ]

            if not buy_orders or not sell_orders:
                return 50.0  # 기본 점수

            # 최고 매수가와 최저 매도가
            max_buy_price = max(o.get("order_price", 0) for o in buy_orders)
            min_sell_price = min(o.get("order_price", float('inf')) for o in sell_orders)

            if min_sell_price == float('inf') or max_buy_price == 0:
                return 50.0

            # 스프레드율 계산
            spread_rate = ((min_sell_price - max_buy_price) / max_buy_price) * 100

            # 스프레드율이 작을수록 높은 점수
            # 0% = 100점, 5% = 75점, 10% = 50점, 20%+ = 0점
            if spread_rate <= 0:
                score = 100.0
            elif spread_rate <= 5:
                score = 100 - (spread_rate * 5)
            elif spread_rate <= 10:
                score = 75 - ((spread_rate - 5) * 5)
            elif spread_rate <= 20:
                score = 50 - ((spread_rate - 10) * 5)
            else:
                score = 0.0

            return max(0.0, min(100.0, score))

        except Exception as e:
            self.logger.warning(f"스프레드 점수 계산 실패: {e}")
            return 50.0

    def _calculate_depth_score(self, song_orders: List[Dict[str, Any]]) -> float:
        """
        주문 깊이 점수 계산

        대기 중인 주문이 많을수록 높은 점수

        Args:
            song_orders: 특정 곡의 주문 데이터

        Returns:
            깊이 점수 (0-100)
        """
        try:
            # 대기 중인 주문 개수
            waiting_orders = [
                o for o in song_orders
                if o.get("order_status") == "대기"
            ]

            waiting_count = len(waiting_orders)

            # 주문 개수에 따른 점수
            # 0개 = 0점, 5개 = 50점, 10개 = 75점, 20개+ = 100점
            if waiting_count == 0:
                score = 0.0
            elif waiting_count <= 5:
                score = waiting_count * 10
            elif waiting_count <= 10:
                score = 50 + ((waiting_count - 5) * 5)
            elif waiting_count <= 20:
                score = 75 + ((waiting_count - 10) * 2.5)
            else:
                score = 100.0

            return max(0.0, min(100.0, score))

        except Exception as e:
            self.logger.warning(f"깊이 점수 계산 실패: {e}")
            return 50.0

    def _calculate_frequency_score(self, song_orders: List[Dict[str, Any]]) -> float:
        """
        갱신 빈도 점수 계산

        최근 주문이 많을수록 높은 점수

        Args:
            song_orders: 특정 곡의 주문 데이터

        Returns:
            빈도 점수 (0-100)
        """
        try:
            now = datetime.now()
            recent_threshold = now - timedelta(minutes=30)  # 최근 30분

            recent_orders = []
            for order in song_orders:
                order_date_str = order.get("order_date")
                if order_date_str:
                    try:
                        order_date = datetime.strptime(order_date_str, "%Y-%m-%d %H:%M:%S")
                        if order_date >= recent_threshold:
                            recent_orders.append(order)
                    except ValueError:
                        continue

            recent_count = len(recent_orders)

            # 최근 30분 주문 개수에 따른 점수
            # 0개 = 0점, 3개 = 50점, 10개+ = 100점
            if recent_count == 0:
                score = 0.0
            elif recent_count <= 3:
                score = recent_count * 16.7
            elif recent_count <= 10:
                score = 50 + ((recent_count - 3) * 7.1)
            else:
                score = 100.0

            return max(0.0, min(100.0, score))

        except Exception as e:
            self.logger.warning(f"빈도 점수 계산 실패: {e}")
            return 50.0

    def calculate_fair_value(
        self,
        order_royalty_rate: float,
        reference_price: Optional[float] = None
    ) -> float:
        """
        공정가치 계산 (최근가 평가 기준)

        공정가치 = 저작권료율 × 기준단가

        Args:
            order_royalty_rate: 1년 수익률 (0.08 = 8%)
            reference_price: 기준단가 (기본값: REFERENCE_PRICE)

        Returns:
            공정가치
        """
        ref_price = reference_price or self.reference_price
        return order_royalty_rate * ref_price

    def generate_signal(
        self,
        spread_rate: Optional[float],
        liquidity_score: float,
        recent_price: Optional[float] = None,
        fair_value: Optional[float] = None
    ) -> str:
        """
        시그널 생성

        조건:
        - 저평가: 스프레드율 -10% 이하 (주문가가 최근가보다 10% 이상 낮음)
        - 고평가: 스프레드율 +10% 이상 (주문가가 최근가보다 10% 이상 높음)
        - 유동성↑: 유동성 점수 > 80
        - 유동성↓: 유동성 점수 < 30
        - 주의: 고평가 + 유동성↓
        - 보통: 그 외

        Args:
            spread_rate: 스프레드율 (%)
            liquidity_score: 유동성 점수
            recent_price: 최근 체결가 (사용 안 함)
            fair_value: 공정가치 (사용 안 함)

        Returns:
            시그널 문자열
        """
        signals = []

        # 스프레드율 기준 평가
        if spread_rate is not None:
            if spread_rate < PREMIUM_THRESHOLD_LOW:  # -10% 이하
                signals.append("저평가")
            elif spread_rate > PREMIUM_THRESHOLD_HIGH:  # +10% 이상
                signals.append("고평가")

        # 유동성 기반 시그널
        if liquidity_score > LIQUIDITY_HIGH_SCORE:
            signals.append("유동성↑")
        elif liquidity_score < LIQUIDITY_LOW_SCORE:
            signals.append("유동성↓")

        # 주의 시그널 (고평가 + 유동성 낮음)
        is_overvalued = "고평가" in signals
        if is_overvalued and liquidity_score < LIQUIDITY_LOW_SCORE:
            return "주의"

        # 시그널 조합
        if signals:
            return ", ".join(signals)
        else:
            return "보통"

    def calculate_order_metrics(
        self,
        order: Dict[str, Any],
        all_orders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        단일 주문의 모든 지표 계산

        Args:
            order: 주문 데이터
            all_orders: 전체 주문 데이터 (유동성 계산용)

        Returns:
            계산된 지표가 포함된 주문 데이터
        """
        try:
            # 기본 정보 추출
            order_price = safe_get(order, "order_price", 0)
            recent_price = safe_get(order, "recent_price", 0)
            order_royalty_rate = safe_get(order, "order_royalty_rate", 0)
            song_name = safe_get(order, "song_name", "")

            # 지표 계산
            spread_rate = self.calculate_spread_rate(order_price, recent_price)
            expected_yield = self.calculate_expected_yield(order_royalty_rate, order_price)
            liquidity_score = self.calculate_liquidity_score(all_orders, song_name)
            fair_value = self.calculate_fair_value(order_royalty_rate)
            signal = self.generate_signal(spread_rate, liquidity_score, recent_price, fair_value)

            # 결과 생성
            result = order.copy()
            result.update({
                "spread_rate": spread_rate,
                "expected_yield": expected_yield,
                "liquidity_score": liquidity_score,
                "fair_value": fair_value,
                "signal": signal
            })

            return result

        except Exception as e:
            self.logger.error(f"지표 계산 실패: {e}")
            return order

    def calculate_price_momentum(
        self,
        all_orders: List[Dict[str, Any]],
        song_name: str
    ) -> Dict[str, Any]:
        """
        가격 모멘텀 지표 계산

        주문가와 최근 체결가의 괴리를 통해 현재 가격 추세 파악

        Args:
            all_orders: 전체 주문 데이터
            song_name: 곡명

        Returns:
            모멘텀 지표 딕셔너리
        """
        try:
            # 해당 곡의 대기 중인 주문만 필터링
            song_orders = [
                o for o in all_orders
                if o.get("song_name") == song_name and o.get("order_status") == "대기"
            ]

            if not song_orders:
                return {
                    "momentum_score": 0.0,
                    "buy_pressure": 0.0,
                    "sell_pressure": 0.0,
                    "waiting_count": 0,
                    "price_range": (0, 0)
                }

            # 최근가 가져오기
            recent_price = safe_get(song_orders[0], "recent_price", 0)
            if recent_price <= 0:
                return {
                    "momentum_score": 0.0,
                    "buy_pressure": 0.0,
                    "sell_pressure": 0.0,
                    "waiting_count": len(song_orders),
                    "price_range": (0, 0)
                }

            # 매수/매도 주문 분리
            buy_orders = [
                o for o in song_orders
                if o.get("order_type") == "구매"
            ]
            sell_orders = [
                o for o in song_orders
                if o.get("order_type") == "판매"
            ]

            # 매수 압력 계산: (최고 매수가 / 최근가 - 1) × 100
            buy_pressure = 0.0
            if buy_orders:
                max_buy_price = max(o.get("order_price", 0) for o in buy_orders)
                buy_pressure = ((max_buy_price / recent_price) - 1) * 100

            # 매도 압력 계산: (최저 매도가 / 최근가 - 1) × 100
            sell_pressure = 0.0
            if sell_orders:
                min_sell_price = min(o.get("order_price", float('inf')) for o in sell_orders)
                if min_sell_price != float('inf'):
                    sell_pressure = ((min_sell_price / recent_price) - 1) * 100

            # 모멘텀 점수 = 매수 압력 - 매도 압력
            momentum_score = buy_pressure - sell_pressure

            # 가격 범위
            all_prices = [o.get("order_price", 0) for o in song_orders]
            price_range = (min(all_prices), max(all_prices))

            return {
                "momentum_score": round(momentum_score, 2),
                "buy_pressure": round(buy_pressure, 2),
                "sell_pressure": round(sell_pressure, 2),
                "waiting_count": len(song_orders),
                "price_range": price_range
            }

        except Exception as e:
            self.logger.warning(f"가격 모멘텀 계산 실패 ({song_name}): {e}")
            return {
                "momentum_score": 0.0,
                "buy_pressure": 0.0,
                "sell_pressure": 0.0,
                "waiting_count": 0,
                "price_range": (0, 0)
            }

    def calculate_batch_metrics(
        self,
        orders: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        배치 주문 지표 계산

        Args:
            orders: 주문 데이터 리스트

        Returns:
            지표가 계산된 주문 데이터 리스트
        """
        try:
            self.logger.info(f"배치 지표 계산 시작: {len(orders)}개 주문")

            results = []
            for i, order in enumerate(orders):
                result = self.calculate_order_metrics(order, orders)
                results.append(result)

                if (i + 1) % 100 == 0:
                    self.logger.info(f"진행: {i + 1}/{len(orders)} 완료")

            self.logger.info(f"배치 지표 계산 완료: {len(results)}개")
            return results

        except Exception as e:
            self.logger.error(f"배치 지표 계산 실패: {e}")
            return orders