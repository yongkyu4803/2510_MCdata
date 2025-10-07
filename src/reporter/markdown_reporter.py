"""
Markdown 리포트 생성기
"""
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from config.settings import REPORTS_DIR, REPORT_TOP_N
from src.utils.logger import setup_logger


class MarkdownReporter:
    """Markdown 형식 일일 리포트 생성"""

    def __init__(self):
        """초기화"""
        self.logger = setup_logger(__name__, "markdown_reporter.log")
        self.reports_dir = REPORTS_DIR
        self.top_n = REPORT_TOP_N

    def generate_daily_report(
        self,
        orders: List[Dict[str, Any]],
        filename: str = None
    ) -> Path:
        """
        일일 종합 리포트 생성

        Args:
            orders: 지표가 계산된 주문 데이터
            filename: 파일명 (기본값: 자동 생성)

        Returns:
            생성된 파일 경로
        """
        try:
            # 파일명 생성
            if filename is None:
                date_str = datetime.now().strftime("%Y%m%d")
                filename = f"daily_report_{date_str}.md"

            filepath = self.reports_dir / filename

            # 리포트 생성
            report_lines = []

            # 헤더
            report_lines.extend(self._generate_header())
            report_lines.append("")

            # 요약 통계
            report_lines.extend(self._generate_summary(orders))
            report_lines.append("")

            # Top 수익률
            report_lines.extend(self._generate_top_yield(orders))
            report_lines.append("")

            # 프리미엄율 상/하위
            report_lines.extend(self._generate_premium_analysis(orders))
            report_lines.append("")

            # 유동성 상/하위
            report_lines.extend(self._generate_liquidity_analysis(orders))
            report_lines.append("")

            # 시그널 분석
            report_lines.extend(self._generate_signal_analysis(orders))
            report_lines.append("")

            # 곡별 통계
            report_lines.extend(self._generate_song_statistics(orders))
            report_lines.append("")

            # 푸터
            report_lines.extend(self._generate_footer())

            # 파일 쓰기
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))

            self.logger.info(f"일일 리포트 생성: {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"리포트 생성 실패: {e}")
            raise

    def _generate_header(self) -> List[str]:
        """리포트 헤더 생성"""
        now = datetime.now()
        lines = [
            "# 🎵 뮤직카우 시장 분석 일일 리포트",
            "",
            f"**생성 일시**: {now.strftime('%Y년 %m월 %d일 %H:%M')}",
            "",
            "---",
        ]
        return lines

    def _generate_summary(self, orders: List[Dict[str, Any]]) -> List[str]:
        """요약 통계 생성"""
        lines = ["## 📊 시장 요약"]
        lines.append("")

        # 전체 통계
        total = len(orders)
        buy_count = sum(1 for o in orders if o.get("order_type") == "구매")
        sell_count = sum(1 for o in orders if o.get("order_type") == "판매")
        waiting_count = sum(1 for o in orders if o.get("order_status") == "대기")

        lines.append(f"- **총 주문 수**: {total:,}개")
        lines.append(f"- **구매 주문**: {buy_count:,}개 ({buy_count/total*100:.1f}%)")
        lines.append(f"- **판매 주문**: {sell_count:,}개 ({sell_count/total*100:.1f}%)")
        lines.append(f"- **대기 주문**: {waiting_count:,}개")
        lines.append("")

        # 지표 통계
        premiums = [o.get("premium") for o in orders if o.get("premium") is not None]
        yields = [o.get("normalized_yield") for o in orders if o.get("normalized_yield") is not None]
        liquidities = [o.get("liquidity_score", 0) for o in orders]

        if premiums:
            avg_premium = sum(premiums) / len(premiums)
            lines.append(f"- **평균 프리미엄율**: {avg_premium:.2f}%")

        if yields:
            avg_yield = sum(yields) / len(yields)
            lines.append(f"- **평균 정규화 수익률**: {avg_yield:.2f}%")

        if liquidities:
            avg_liquidity = sum(liquidities) / len(liquidities)
            lines.append(f"- **평균 유동성 점수**: {avg_liquidity:.1f}/100")

        lines.append("")
        lines.append("---")

        return lines

    def _generate_top_yield(self, orders: List[Dict[str, Any]]) -> List[str]:
        """고수익률 주문 섹션 생성"""
        lines = [f"## 💰 고수익률 주문 (Top {self.top_n})"]
        lines.append("")

        # 대기 중인 주문만 필터링
        waiting_orders = [
            o for o in orders
            if o.get("order_status") == "대기" and o.get("normalized_yield") is not None
        ]

        # 수익률 높은 순 정렬
        top_yields = sorted(
            waiting_orders,
            key=lambda x: x.get("normalized_yield", 0),
            reverse=True
        )[:self.top_n]

        if top_yields:
            lines.append("| 순위 | 곡명 | 아티스트 | 수익률 | 프리미엄율 | 유동성 | 시그널 |")
            lines.append("|------|------|----------|--------|--------|--------|--------|")

            for i, order in enumerate(top_yields, 1):
                song = order.get("song_name", "")[:20]
                artist = order.get("song_artist", "")[:15]
                yield_val = order.get("normalized_yield", 0)
                premium = order.get("premium", 0)
                liquidity = order.get("liquidity_score", 0)
                signal = order.get("signal", "")

                lines.append(
                    f"| {i} | {song} | {artist} | {yield_val:.2f}% | "
                    f"{premium:.2f}% | {liquidity:.1f} | {signal} |"
                )
        else:
            lines.append("*대기 중인 주문이 없습니다.*")

        lines.append("")
        lines.append("---")

        return lines

    def _generate_premium_analysis(self, orders: List[Dict[str, Any]]) -> List[str]:
        """프리미엄율 분석 섹션 생성"""
        lines = [f"## 📈 프리미엄율 분석 (상위/하위 {self.top_n}개)"]
        lines.append("")

        # 대기 중인 주문만 필터링
        waiting_orders = [
            o for o in orders
            if o.get("order_status") == "대기" and o.get("premium") is not None
        ]

        # 프리미엄율 기준 정렬
        sorted_by_premium = sorted(
            waiting_orders,
            key=lambda x: x.get("premium", 0)
        )

        # 하위 N개 (저평가)
        lines.append(f"### 🔽 저평가 주문 (프리미엄율 낮은 순)")
        lines.append("")

        low_premium = sorted_by_premium[:self.top_n]
        if low_premium:
            lines.append("| 순위 | 곡명 | 아티스트 | 프리미엄율 | 수익률 | 시그널 |")
            lines.append("|------|------|----------|--------|--------|--------|")

            for i, order in enumerate(low_premium, 1):
                song = order.get("song_name", "")[:20]
                artist = order.get("song_artist", "")[:15]
                premium = order.get("premium", 0)
                yield_val = order.get("normalized_yield", 0)
                signal = order.get("signal", "")

                lines.append(
                    f"| {i} | {song} | {artist} | {premium:.2f}% | "
                    f"{yield_val:.2f}% | {signal} |"
                )
        else:
            lines.append("*데이터 없음*")

        lines.append("")

        # 상위 N개 (고평가)
        lines.append(f"### 🔼 고평가 주문 (프리미엄율 높은 순)")
        lines.append("")

        high_premium = sorted_by_premium[-self.top_n:][::-1]
        if high_premium:
            lines.append("| 순위 | 곡명 | 아티스트 | 프리미엄율 | 수익률 | 시그널 |")
            lines.append("|------|------|----------|--------|--------|--------|")

            for i, order in enumerate(high_premium, 1):
                song = order.get("song_name", "")[:20]
                artist = order.get("song_artist", "")[:15]
                premium = order.get("premium", 0)
                yield_val = order.get("normalized_yield", 0)
                signal = order.get("signal", "")

                lines.append(
                    f"| {i} | {song} | {artist} | {premium:.2f}% | "
                    f"{yield_val:.2f}% | {signal} |"
                )
        else:
            lines.append("*데이터 없음*")

        lines.append("")
        lines.append("---")

        return lines

    def _generate_liquidity_analysis(self, orders: List[Dict[str, Any]]) -> List[str]:
        """유동성 분석 섹션 생성"""
        lines = [f"## 💧 유동성 분석"]
        lines.append("")

        # 유동성 점수 기준 정렬
        sorted_by_liquidity = sorted(
            orders,
            key=lambda x: x.get("liquidity_score", 0),
            reverse=True
        )

        # 상위 N개 (고유동성)
        lines.append(f"### ⬆️ 고유동성 곡 (Top {self.top_n})")
        lines.append("")

        high_liquidity = sorted_by_liquidity[:self.top_n]
        if high_liquidity:
            lines.append("| 순위 | 곡명 | 아티스트 | 유동성 | 프리미엄율 | 시그널 |")
            lines.append("|------|------|----------|--------|--------|--------|")

            for i, order in enumerate(high_liquidity, 1):
                song = order.get("song_name", "")[:20]
                artist = order.get("song_artist", "")[:15]
                liquidity = order.get("liquidity_score", 0)
                premium = order.get("premium", 0) if order.get("premium") is not None else 0
                signal = order.get("signal", "")

                lines.append(
                    f"| {i} | {song} | {artist} | {liquidity:.1f} | "
                    f"{premium:.2f}% | {signal} |"
                )
        else:
            lines.append("*데이터 없음*")

        lines.append("")
        lines.append("---")

        return lines

    def _generate_signal_analysis(self, orders: List[Dict[str, Any]]) -> List[str]:
        """시그널 분석 섹션 생성"""
        lines = ["## 🚨 시그널 분석"]
        lines.append("")

        # 시그널별 카운트
        signal_counts = {}
        for order in orders:
            signal = order.get("signal", "Unknown")
            signal_counts[signal] = signal_counts.get(signal, 0) + 1

        # 테이블 생성
        lines.append("| 시그널 | 개수 | 비율 |")
        lines.append("|--------|------|------|")

        total = len(orders)
        for signal, count in sorted(signal_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = count / total * 100
            lines.append(f"| {signal} | {count:,}개 | {percentage:.1f}% |")

        lines.append("")
        lines.append("---")

        return lines

    def _generate_song_statistics(self, orders: List[Dict[str, Any]]) -> List[str]:
        """곡별 통계 섹션 생성"""
        lines = ["## 🎼 거래량 상위 곡"]
        lines.append("")

        # 곡별 주문 수 카운트
        song_counts = {}
        for order in orders:
            song = order.get("song_name", "Unknown")
            artist = order.get("song_artist", "Unknown")
            key = (song, artist)

            if key not in song_counts:
                song_counts[key] = 0
            song_counts[key] += 1

        # 상위 10개
        top_songs = sorted(song_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        if top_songs:
            lines.append("| 순위 | 곡명 | 아티스트 | 주문 수 |")
            lines.append("|------|------|----------|---------|")

            for i, ((song, artist), count) in enumerate(top_songs, 1):
                lines.append(f"| {i} | {song[:25]} | {artist[:15]} | {count}개 |")
        else:
            lines.append("*데이터 없음*")

        lines.append("")
        lines.append("---")

        return lines

    def _generate_footer(self) -> List[str]:
        """리포트 푸터 생성"""
        now = datetime.now()
        lines = [
            "",
            "---",
            "",
            "*본 리포트는 자동 생성되었습니다.*",
            "",
            f"*생성 시각: {now.strftime('%Y-%m-%d %H:%M:%S')}*"
        ]
        return lines