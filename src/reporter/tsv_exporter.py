"""
TSV 출력 모듈 (스프레드시트 호환)
"""
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from config.settings import TSV_DELIMITER, REPORTS_DIR, DATE_FORMAT
from src.utils.logger import setup_logger


class TSVExporter:
    """TSV 형식으로 데이터 출력"""

    def __init__(self):
        """초기화"""
        self.logger = setup_logger(__name__, "tsv_exporter.log")
        self.delimiter = TSV_DELIMITER
        self.reports_dir = REPORTS_DIR

    def export_to_tsv(
        self,
        orders: List[Dict[str, Any]],
        filename: str = None,
        include_headers: bool = True
    ) -> Path:
        """
        주문 데이터를 TSV 형식으로 출력

        Args:
            orders: 지표가 계산된 주문 데이터
            filename: 파일명 (기본값: 자동 생성)
            include_headers: 헤더 포함 여부

        Returns:
            생성된 파일 경로
        """
        try:
            # 파일명 생성
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                filename = f"market_summary_{timestamp}.tsv"

            filepath = self.reports_dir / filename

            # TSV 데이터 생성
            lines = []

            # 헤더
            if include_headers:
                headers = [
                    "time",
                    "song",
                    "artist",
                    "side",
                    "price",
                    "recent",
                    "yield(%)",
                    "premium(%)",
                    "liquidity",
                    "signal",
                    "url"
                ]
                lines.append(self.delimiter.join(headers))

            # 데이터 행
            for order in orders:
                row = self._format_order_row(order)
                lines.append(row)

            # 파일 쓰기
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            self.logger.info(f"TSV 파일 생성: {filepath} ({len(orders)}개 주문)")
            return filepath

        except Exception as e:
            self.logger.error(f"TSV 출력 실패: {e}")
            raise

    def _format_order_row(self, order: Dict[str, Any]) -> str:
        """
        주문 데이터를 TSV 행으로 포맷팅

        Args:
            order: 주문 데이터

        Returns:
            TSV 형식 문자열
        """
        try:
            # 각 필드 추출 및 포맷팅
            time = order.get("order_date", "")
            song = order.get("song_name", "")
            artist = order.get("song_artist", "")
            side = order.get("order_type", "")
            price = order.get("order_price", 0)
            recent = order.get("recent_price", 0)

            # 계산된 지표
            yield_val = order.get("normalized_yield")
            premium = order.get("premium")
            liquidity = order.get("liquidity_score", 0)
            signal = order.get("signal", "")
            url = order.get("url_link", "")

            # 숫자 포맷팅
            yield_str = f"{yield_val:.2f}" if yield_val is not None else ""
            premium_str = f"{premium:.2f}" if premium is not None else ""
            liquidity_str = f"{liquidity:.1f}"

            # TSV 행 생성
            row_data = [
                time,
                song,
                artist,
                side,
                str(price),
                str(recent),
                yield_str,
                premium_str,
                liquidity_str,
                signal,
                url
            ]

            return self.delimiter.join(row_data)

        except Exception as e:
            self.logger.warning(f"행 포맷팅 실패: {e}")
            return ""

    def export_filtered_orders(
        self,
        orders: List[Dict[str, Any]],
        filter_type: str = "waiting",
        filename: str = None
    ) -> Path:
        """
        필터링된 주문만 TSV로 출력

        Args:
            orders: 전체 주문 데이터
            filter_type: 필터 타입 (waiting, completed, buy, sell, signal)
            filename: 파일명

        Returns:
            생성된 파일 경로
        """
        try:
            # 필터링
            if filter_type == "waiting":
                filtered = [o for o in orders if o.get("order_status") == "대기"]
            elif filter_type == "completed":
                filtered = [o for o in orders if o.get("order_status") in ["완료", "체결"]]
            elif filter_type == "buy":
                filtered = [o for o in orders if o.get("order_type") == "구매"]
            elif filter_type == "sell":
                filtered = [o for o in orders if o.get("order_type") == "판매"]
            elif filter_type == "undervalued":
                filtered = [o for o in orders if "저평가" in o.get("signal", "")]
            elif filter_type == "overvalued":
                filtered = [o for o in orders if "고평가" in o.get("signal", "")]
            elif filter_type == "alert":
                filtered = [o for o in orders if o.get("signal", "") in ["주의", "저평가", "고평가"]]
            else:
                filtered = orders

            self.logger.info(f"필터링 완료: {len(filtered)}/{len(orders)} ({filter_type})")

            # TSV 출력
            return self.export_to_tsv(filtered, filename)

        except Exception as e:
            self.logger.error(f"필터링 출력 실패: {e}")
            raise

    def export_top_orders(
        self,
        orders: List[Dict[str, Any]],
        sort_by: str = "premium",
        top_n: int = 10,
        ascending: bool = True,
        filename: str = None
    ) -> Path:
        """
        상위/하위 주문만 TSV로 출력

        Args:
            orders: 전체 주문 데이터
            sort_by: 정렬 기준 (premium, yield, liquidity)
            top_n: 상위 N개
            ascending: 오름차순 여부
            filename: 파일명

        Returns:
            생성된 파일 경로
        """
        try:
            # 정렬 키 매핑
            sort_key_map = {
                "premium": "premium",
                "yield": "normalized_yield",
                "liquidity": "liquidity_score"
            }

            sort_key = sort_key_map.get(sort_by, "premium")

            # 정렬 (None 값 필터링)
            valid_orders = [o for o in orders if o.get(sort_key) is not None]
            sorted_orders = sorted(
                valid_orders,
                key=lambda x: x.get(sort_key, 0),
                reverse=not ascending
            )

            # 상위 N개 추출
            top_orders = sorted_orders[:top_n]

            self.logger.info(f"상위 {top_n}개 추출 완료 (정렬: {sort_by}, {'오름차순' if ascending else '내림차순'})")

            # TSV 출력
            return self.export_to_tsv(top_orders, filename)

        except Exception as e:
            self.logger.error(f"상위 주문 출력 실패: {e}")
            raise

    def export_summary_by_song(
        self,
        orders: List[Dict[str, Any]],
        filename: str = None
    ) -> Path:
        """
        곡별 요약 통계 TSV 출력

        Args:
            orders: 전체 주문 데이터
            filename: 파일명

        Returns:
            생성된 파일 경로
        """
        try:
            # 곡별 그룹화
            song_stats = {}

            for order in orders:
                song = order.get("song_name", "Unknown")
                if song not in song_stats:
                    song_stats[song] = {
                        "artist": order.get("song_artist", ""),
                        "buy_count": 0,
                        "sell_count": 0,
                        "avg_premium": [],
                        "avg_yield": [],
                        "liquidity": order.get("liquidity_score", 0)
                    }

                # 통계 누적
                if order.get("order_type") == "구매":
                    song_stats[song]["buy_count"] += 1
                elif order.get("order_type") == "판매":
                    song_stats[song]["sell_count"] += 1

                if order.get("premium") is not None:
                    song_stats[song]["avg_premium"].append(order["premium"])
                if order.get("normalized_yield") is not None:
                    song_stats[song]["avg_yield"].append(order["normalized_yield"])

            # TSV 데이터 생성
            lines = []

            # 헤더
            headers = [
                "song",
                "artist",
                "buy_orders",
                "sell_orders",
                "avg_premium(%)",
                "avg_yield(%)",
                "liquidity"
            ]
            lines.append(self.delimiter.join(headers))

            # 데이터 행
            for song, stats in sorted(song_stats.items()):
                avg_premium = sum(stats["avg_premium"]) / len(stats["avg_premium"]) if stats["avg_premium"] else 0
                avg_yield = sum(stats["avg_yield"]) / len(stats["avg_yield"]) if stats["avg_yield"] else 0

                row = [
                    song,
                    stats["artist"],
                    str(stats["buy_count"]),
                    str(stats["sell_count"]),
                    f"{avg_premium:.2f}",
                    f"{avg_yield:.2f}",
                    f"{stats['liquidity']:.1f}"
                ]
                lines.append(self.delimiter.join(row))

            # 파일명 생성
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                filename = f"song_summary_{timestamp}.tsv"

            filepath = self.reports_dir / filename

            # 파일 쓰기
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            self.logger.info(f"곡별 요약 TSV 생성: {filepath} ({len(song_stats)}곡)")
            return filepath

        except Exception as e:
            self.logger.error(f"곡별 요약 출력 실패: {e}")
            raise