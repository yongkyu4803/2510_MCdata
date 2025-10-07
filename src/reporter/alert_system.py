"""
실시간 알림 시스템
"""
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from config.settings import (
    ALERT_PREMIUM_THRESHOLD,
    ALERT_YIELD_CHANGE,
    ALERT_TIME_WINDOW,
    SLACK_WEBHOOK_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID
)
from src.utils.logger import setup_logger


class AlertSystem:
    """실시간 알림 시스템"""

    def __init__(self):
        """초기화"""
        self.logger = setup_logger(__name__, "alert_system.log")
        self.alert_premium_threshold = ALERT_PREMIUM_THRESHOLD
        self.alert_yield_change = ALERT_YIELD_CHANGE
        self.time_window = ALERT_TIME_WINDOW

        # 알림 이력 (중복 방지용)
        self.alert_history = {}

    def check_alerts(
        self,
        orders: List[Dict[str, Any]],
        previous_orders: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        알림 조건 체크

        Args:
            orders: 현재 주문 데이터
            previous_orders: 이전 주문 데이터 (수익률 변동 체크용)

        Returns:
            알림 목록
        """
        alerts = []

        # 1. 프리미엄율 알림
        premium_alerts = self._check_premium_alerts(orders)
        alerts.extend(premium_alerts)

        # 2. 수익률 변동 알림
        if previous_orders:
            yield_alerts = self._check_yield_change_alerts(orders, previous_orders)
            alerts.extend(yield_alerts)

        # 3. 시그널 기반 알림
        signal_alerts = self._check_signal_alerts(orders)
        alerts.extend(signal_alerts)

        # 알림 로깅
        if alerts:
            self.logger.info(f"총 {len(alerts)}개 알림 생성")
            for alert in alerts:
                self.logger.info(f"  - {alert['type']}: {alert['message']}")

        return alerts

    def _check_premium_alerts(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        프리미엄율 알림 체크

        조건: 프리미엄율 > ±3%

        Args:
            orders: 주문 데이터

        Returns:
            알림 목록
        """
        alerts = []

        for order in orders:
            # 대기 주문만 체크
            if order.get("order_status") != "대기":
                continue

            premium = order.get("premium")
            if premium is None:
                continue

            # 프리미엄율 기준 체크
            if abs(premium) > self.alert_premium_threshold:
                # 중복 체크
                order_no = order.get("order_no")
                if not self._is_duplicate_alert(order_no, "premium"):
                    alert = {
                        "type": "premium",
                        "severity": "high" if abs(premium) > 5 else "medium",
                        "message": f"프리미엄율 {premium:.2f}% - {order.get('song_name', 'Unknown')}",
                        "order": order,
                        "timestamp": datetime.now().isoformat()
                    }
                    alerts.append(alert)
                    self._add_to_history(order_no, "premium")

        return alerts

    def _check_yield_change_alerts(
        self,
        orders: List[Dict[str, Any]],
        previous_orders: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        수익률 변동 알림 체크

        조건: 10분 내 수익률 변동 > 2%

        Args:
            orders: 현재 주문 데이터
            previous_orders: 이전 주문 데이터

        Returns:
            알림 목록
        """
        alerts = []

        # 이전 주문을 딕셔너리로 변환 (order_no 기준)
        prev_dict = {o.get("order_no"): o for o in previous_orders}

        for order in orders:
            order_no = order.get("order_no")
            if order_no not in prev_dict:
                continue

            prev_order = prev_dict[order_no]

            # 수익률 비교
            current_yield = order.get("normalized_yield")
            prev_yield = prev_order.get("normalized_yield")

            if current_yield is None or prev_yield is None:
                continue

            yield_change = abs(current_yield - prev_yield)

            if yield_change > self.alert_yield_change:
                # 시간 윈도우 체크
                order_time = datetime.strptime(order.get("order_date", ""), "%Y-%m-%d %H:%M:%S")
                prev_time = datetime.strptime(prev_order.get("order_date", ""), "%Y-%m-%d %H:%M:%S")

                time_diff = (order_time - prev_time).total_seconds() / 60

                if time_diff <= self.time_window:
                    if not self._is_duplicate_alert(order_no, "yield_change"):
                        alert = {
                            "type": "yield_change",
                            "severity": "high",
                            "message": f"수익률 {yield_change:.2f}% 변동 - {order.get('song_name', 'Unknown')}",
                            "order": order,
                            "change": yield_change,
                            "timestamp": datetime.now().isoformat()
                        }
                        alerts.append(alert)
                        self._add_to_history(order_no, "yield_change")

        return alerts

    def _check_signal_alerts(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        시그널 기반 알림 체크

        조건: 주의, 저평가, 고평가 시그널

        Args:
            orders: 주문 데이터

        Returns:
            알림 목록
        """
        alerts = []

        for order in orders:
            signal = order.get("signal", "")

            # 알림 대상 시그널
            if signal in ["주의", "저평가", "고평가"]:
                order_no = order.get("order_no")

                if not self._is_duplicate_alert(order_no, "signal"):
                    severity_map = {
                        "주의": "high",
                        "저평가": "medium",
                        "고평가": "low"
                    }

                    alert = {
                        "type": "signal",
                        "severity": severity_map.get(signal, "low"),
                        "message": f"시그널: {signal} - {order.get('song_name', 'Unknown')}",
                        "order": order,
                        "timestamp": datetime.now().isoformat()
                    }
                    alerts.append(alert)
                    self._add_to_history(order_no, "signal")

        return alerts

    def _is_duplicate_alert(self, order_no: str, alert_type: str) -> bool:
        """
        중복 알림 체크

        Args:
            order_no: 주문 번호
            alert_type: 알림 타입

        Returns:
            중복 여부
        """
        key = f"{order_no}_{alert_type}"

        if key in self.alert_history:
            # 1시간 이내 중복 알림 방지
            last_time = self.alert_history[key]
            if datetime.now() - last_time < timedelta(hours=1):
                return True

        return False

    def _add_to_history(self, order_no: str, alert_type: str):
        """
        알림 이력 추가

        Args:
            order_no: 주문 번호
            alert_type: 알림 타입
        """
        key = f"{order_no}_{alert_type}"
        self.alert_history[key] = datetime.now()

    def send_alerts(
        self,
        alerts: List[Dict[str, Any]],
        channels: List[str] = ["console"]
    ) -> bool:
        """
        알림 발송

        Args:
            alerts: 알림 목록
            channels: 발송 채널 (console, slack, telegram)

        Returns:
            발송 성공 여부
        """
        if not alerts:
            return True

        success = True

        for channel in channels:
            if channel == "console":
                success &= self._send_console_alerts(alerts)
            elif channel == "slack" and SLACK_WEBHOOK_URL:
                success &= self._send_slack_alerts(alerts)
            elif channel == "telegram" and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                success &= self._send_telegram_alerts(alerts)

        return success

    def _send_console_alerts(self, alerts: List[Dict[str, Any]]) -> bool:
        """콘솔 알림 출력"""
        try:
            print("\n" + "=" * 60)
            print(f"🚨 알림: {len(alerts)}건")
            print("=" * 60)

            for i, alert in enumerate(alerts, 1):
                severity_icon = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(alert["severity"], "⚪")

                print(f"{i}. {severity_icon} [{alert['type']}] {alert['message']}")

                # 상세 정보
                order = alert.get("order", {})
                if order:
                    print(f"   - 가격: {order.get('order_price', 0):,}원")
                    print(f"   - 프리미엄율: {order.get('premium', 0):.2f}%")
                    print(f"   - 수익률: {order.get('normalized_yield', 0):.2f}%")

            print("=" * 60)

            return True

        except Exception as e:
            self.logger.error(f"콘솔 알림 실패: {e}")
            return False

    def _send_slack_alerts(self, alerts: List[Dict[str, Any]]) -> bool:
        """Slack 알림 발송"""
        try:
            if not SLACK_WEBHOOK_URL:
                return False

            # Slack 메시지 포맷팅
            text = f"🚨 뮤직카우 알림: {len(alerts)}건\n\n"

            for alert in alerts[:5]:  # 최대 5개만 표시
                text += f"• [{alert['type']}] {alert['message']}\n"

            payload = {"text": text}

            response = requests.post(
                SLACK_WEBHOOK_URL,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                self.logger.info("Slack 알림 발송 성공")
                return True
            else:
                self.logger.error(f"Slack 알림 실패: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Slack 알림 오류: {e}")
            return False

    def _send_telegram_alerts(self, alerts: List[Dict[str, Any]]) -> bool:
        """Telegram 알림 발송"""
        try:
            if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
                return False

            # Telegram 메시지 포맷팅
            text = f"🚨 뮤직카우 알림: {len(alerts)}건\n\n"

            for alert in alerts[:5]:  # 최대 5개만 표시
                text += f"• [{alert['type']}] {alert['message']}\n"

            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                self.logger.info("Telegram 알림 발송 성공")
                return True
            else:
                self.logger.error(f"Telegram 알림 실패: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Telegram 알림 오류: {e}")
            return False

    def clear_history(self, hours: int = 24):
        """
        알림 이력 정리

        Args:
            hours: 유지 시간 (기본 24시간)
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        keys_to_remove = [
            key for key, timestamp in self.alert_history.items()
            if timestamp < cutoff_time
        ]

        for key in keys_to_remove:
            del self.alert_history[key]

        self.logger.info(f"알림 이력 정리: {len(keys_to_remove)}개 제거")