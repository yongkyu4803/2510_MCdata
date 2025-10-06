"""
데이터 수집기
"""
import json
import time
import schedule
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.settings import (
    RAW_DATA_DIR,
    COLLECTION_INTERVAL_MINUTES,
    DAILY_REPORT_TIME,
    FILE_DATE_FORMAT,
    DATE_FORMAT
)
from src.collector.api_client import MusicowAPIClient
from src.utils.logger import setup_logger
from src.utils.helpers import save_json, load_json, get_timestamp, remove_duplicates


class DataCollector:
    """데이터 수집기"""

    def __init__(self):
        """초기화"""
        self.logger = setup_logger(__name__, "data_collector.log")
        self.api_client = MusicowAPIClient()
        self.raw_data_dir = RAW_DATA_DIR
        self.is_running = False

        # 오늘 날짜로 디렉토리 생성
        self.today = datetime.now().strftime("%Y%m%d")
        self.today_dir = self.raw_data_dir / self.today
        self.today_dir.mkdir(parents=True, exist_ok=True)

        # 일일 데이터 누적 (중복 제거용)
        self.daily_orders = {}

    def collect_data(self) -> bool:
        """
        데이터 수집 메인 함수

        Returns:
            수집 성공 여부
        """
        try:
            self.logger.info("데이터 수집 시작")

            # API에서 데이터 가져오기
            orders = self.api_client.get_validated_orders()
            if not orders:
                self.logger.warning("수집된 데이터가 없습니다")
                return False

            # 타임스탬프 생성
            timestamp = get_timestamp(FILE_DATE_FORMAT)

            # 파일명 생성
            filename = f"{timestamp}_orders.json"
            filepath = self.today_dir / filename

            # 데이터 저장
            if save_json(orders, filepath):
                self.logger.info(f"데이터 저장 완료: {filepath} ({len(orders)}개)")

                # 일일 데이터 누적 (중복 제거)
                self._accumulate_daily_orders(orders)

                # 통계 로깅
                self._log_statistics(orders)

                return True
            else:
                self.logger.error("데이터 저장 실패")
                return False

        except Exception as e:
            self.logger.error(f"데이터 수집 중 오류: {e}")
            return False

    def _accumulate_daily_orders(self, orders: List[Dict[str, Any]]):
        """
        일일 주문 데이터 누적 (중복 제거)

        Args:
            orders: 새로운 주문 데이터
        """
        for order in orders:
            order_no = order.get("order_no")
            if order_no:
                # 최신 데이터로 업데이트
                self.daily_orders[order_no] = order

        self.logger.info(f"일일 누적 주문: {len(self.daily_orders)}개 (중복 제거)")

    def _log_statistics(self, orders: List[Dict[str, Any]]):
        """
        수집 데이터 통계 로깅

        Args:
            orders: 주문 데이터
        """
        try:
            buy_count = sum(1 for o in orders if o.get("order_type") == "구매")
            sell_count = sum(1 for o in orders if o.get("order_type") == "판매")
            wait_count = sum(1 for o in orders if o.get("order_status") == "대기")
            done_count = sum(1 for o in orders if o.get("order_status") in ["완료", "체결"])

            self.logger.info(
                f"수집 통계 - 총: {len(orders)}, "
                f"구매: {buy_count}, 판매: {sell_count}, "
                f"대기: {wait_count}, 완료/체결: {done_count}"
            )
        except Exception as e:
            self.logger.warning(f"통계 로깅 실패: {e}")

    def save_daily_summary(self):
        """일일 요약 데이터 저장"""
        try:
            if not self.daily_orders:
                self.logger.warning("저장할 일일 데이터가 없습니다")
                return

            # 일일 요약 파일 저장
            summary_file = self.raw_data_dir / f"{self.today}_daily_summary.json"
            orders_list = list(self.daily_orders.values())

            if save_json(orders_list, summary_file):
                self.logger.info(f"일일 요약 저장 완료: {summary_file} ({len(orders_list)}개)")

                # 일일 통계 로깅
                self._log_daily_statistics(orders_list)
            else:
                self.logger.error("일일 요약 저장 실패")

        except Exception as e:
            self.logger.error(f"일일 요약 저장 중 오류: {e}")

    def _log_daily_statistics(self, orders: List[Dict[str, Any]]):
        """
        일일 통계 로깅

        Args:
            orders: 일일 전체 주문 데이터
        """
        try:
            # 곡별 거래 통계
            song_stats = {}
            for order in orders:
                song = order.get("song_name", "Unknown")
                if song not in song_stats:
                    song_stats[song] = {"구매": 0, "판매": 0, "대기": 0}

                order_type = order.get("order_type", "")
                if order_type in ["구매", "판매"]:
                    song_stats[song][order_type] += 1

                if order.get("order_status") == "대기":
                    song_stats[song]["대기"] += 1

            # 상위 10개 곡
            top_songs = sorted(
                song_stats.items(),
                key=lambda x: x[1]["구매"] + x[1]["판매"],
                reverse=True
            )[:10]

            self.logger.info("=== 일일 거래 상위 10개 곡 ===")
            for i, (song, stats) in enumerate(top_songs, 1):
                total = stats["구매"] + stats["판매"]
                self.logger.info(
                    f"{i:2}. {song[:20]:20} | "
                    f"총 {total:3}건 (구매: {stats['구매']}, 판매: {stats['판매']}, 대기: {stats['대기']})"
                )

        except Exception as e:
            self.logger.warning(f"일일 통계 로깅 실패: {e}")

    def start_scheduler(self):
        """스케줄러 시작"""
        try:
            self.logger.info(f"스케줄러 시작 - {COLLECTION_INTERVAL_MINUTES}분 간격")

            # 즉시 한 번 실행
            self.collect_data()

            # 정기 수집 스케줄 설정
            schedule.every(COLLECTION_INTERVAL_MINUTES).minutes.do(self.collect_data)

            # 일일 리포트 스케줄 설정
            schedule.every().day.at(DAILY_REPORT_TIME).do(self.save_daily_summary)

            # 자정에 새 디렉토리 생성
            schedule.every().day.at("00:00").do(self._reset_daily_data)

            self.is_running = True

            # 스케줄 실행
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("사용자가 스케줄러를 중지했습니다")
            self.stop_scheduler()
        except Exception as e:
            self.logger.error(f"스케줄러 오류: {e}")
            self.stop_scheduler()

    def _reset_daily_data(self):
        """일일 데이터 초기화 (자정)"""
        try:
            # 이전 날짜 요약 저장
            self.save_daily_summary()

            # 새 날짜로 초기화
            self.today = datetime.now().strftime("%Y%m%d")
            self.today_dir = self.raw_data_dir / self.today
            self.today_dir.mkdir(parents=True, exist_ok=True)

            # 일일 데이터 초기화
            self.daily_orders = {}

            self.logger.info(f"일일 데이터 초기화 완료: {self.today}")

        except Exception as e:
            self.logger.error(f"일일 데이터 초기화 실패: {e}")

    def stop_scheduler(self):
        """스케줄러 중지"""
        self.is_running = False

        # 마지막 요약 저장
        self.save_daily_summary()

        # API 클라이언트 종료
        self.api_client.close()

        self.logger.info("스케줄러 중지 완료")

    def collect_once(self) -> bool:
        """
        1회성 데이터 수집 (테스트용)

        Returns:
            수집 성공 여부
        """
        result = self.collect_data()
        self.api_client.close()
        return result