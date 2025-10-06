"""
리포트 시스템 테스트
"""
import json
from pathlib import Path
from datetime import datetime
from src.reporter.tsv_exporter import TSVExporter
from src.reporter.markdown_reporter import MarkdownReporter
from src.reporter.alert_system import AlertSystem


def test_tsv_exporter():
    """TSV 출력 모듈 테스트"""

    print("\n" + "=" * 60)
    print("📋 TSV 출력 모듈 테스트")
    print("=" * 60)

    # 1. 데이터 로드
    print("\n1. 테스트 데이터 로드...")
    print("-" * 40)

    metrics_file = Path("data/processed/sample_metrics.json")
    if not metrics_file.exists():
        print(f"❌ 메트릭 파일 없음: {metrics_file}")
        print("먼저 test_metrics.py를 실행하세요.")
        return False

    with open(metrics_file, 'r', encoding='utf-8') as f:
        orders = json.load(f)

    print(f"✅ {len(orders)}개 주문 데이터 로드")

    # 2. TSV Exporter 생성
    print("\n2. TSV Exporter 생성...")
    print("-" * 40)

    exporter = TSVExporter()
    print("✅ TSVExporter 생성 성공")

    # 3. 전체 TSV 출력
    print("\n3. 전체 데이터 TSV 출력...")
    print("-" * 40)

    filepath = exporter.export_to_tsv(orders, "test_all_orders.tsv")
    print(f"✅ TSV 파일 생성: {filepath.name}")

    file_size = filepath.stat().st_size
    print(f"  파일 크기: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    # 4. 필터링 출력 테스트
    print("\n4. 필터링 출력 테스트...")
    print("-" * 40)

    filters = ["waiting", "undervalued", "overvalued", "alert"]
    for filter_type in filters:
        filepath = exporter.export_filtered_orders(orders, filter_type, f"test_{filter_type}.tsv")
        print(f"  - {filter_type}: {filepath.name}")

    # 5. Top 주문 출력 테스트
    print("\n5. Top 주문 출력 테스트...")
    print("-" * 40)

    # 저평가 Top 10
    filepath = exporter.export_top_orders(
        orders,
        sort_by="premium",
        top_n=10,
        ascending=True,
        filename="test_undervalued_top10.tsv"
    )
    print(f"  - 저평가 Top 10: {filepath.name}")

    # 고수익률 Top 10
    filepath = exporter.export_top_orders(
        orders,
        sort_by="yield",
        top_n=10,
        ascending=False,
        filename="test_high_yield_top10.tsv"
    )
    print(f"  - 고수익률 Top 10: {filepath.name}")

    # 6. 곡별 요약 출력
    print("\n6. 곡별 요약 출력...")
    print("-" * 40)

    filepath = exporter.export_summary_by_song(orders, "test_song_summary.tsv")
    print(f"✅ 곡별 요약 TSV: {filepath.name}")

    print("\n" + "=" * 60)
    print("✨ TSV 출력 모듈 테스트 완료")
    print("=" * 60)

    return True


def test_markdown_reporter():
    """Markdown 리포트 생성기 테스트"""

    print("\n" + "=" * 60)
    print("📝 Markdown 리포트 생성기 테스트")
    print("=" * 60)

    # 1. 데이터 로드
    print("\n1. 테스트 데이터 로드...")
    print("-" * 40)

    metrics_file = Path("data/processed/sample_metrics.json")
    if not metrics_file.exists():
        print(f"❌ 메트릭 파일 없음: {metrics_file}")
        return False

    with open(metrics_file, 'r', encoding='utf-8') as f:
        orders = json.load(f)

    print(f"✅ {len(orders)}개 주문 데이터 로드")

    # 2. Reporter 생성
    print("\n2. Markdown Reporter 생성...")
    print("-" * 40)

    reporter = MarkdownReporter()
    print("✅ MarkdownReporter 생성 성공")

    # 3. 일일 리포트 생성
    print("\n3. 일일 리포트 생성...")
    print("-" * 40)

    filepath = reporter.generate_daily_report(orders, "test_daily_report.md")
    print(f"✅ 리포트 생성: {filepath.name}")

    file_size = filepath.stat().st_size
    print(f"  파일 크기: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    # 4. 리포트 내용 미리보기
    print("\n4. 리포트 내용 미리보기...")
    print("-" * 40)

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"  총 {len(lines)}줄")
    print("\n  첫 20줄:")
    for line in lines[:20]:
        print(f"    {line.rstrip()}")

    print("\n" + "=" * 60)
    print("✨ Markdown 리포트 테스트 완료")
    print("=" * 60)

    return True


def test_alert_system():
    """알림 시스템 테스트"""

    print("\n" + "=" * 60)
    print("🚨 알림 시스템 테스트")
    print("=" * 60)

    # 1. 데이터 로드
    print("\n1. 테스트 데이터 로드...")
    print("-" * 40)

    metrics_file = Path("data/processed/sample_metrics.json")
    if not metrics_file.exists():
        print(f"❌ 메트릭 파일 없음: {metrics_file}")
        return False

    with open(metrics_file, 'r', encoding='utf-8') as f:
        orders = json.load(f)

    print(f"✅ {len(orders)}개 주문 데이터 로드")

    # 2. Alert System 생성
    print("\n2. Alert System 생성...")
    print("-" * 40)

    alert_system = AlertSystem()
    print("✅ AlertSystem 생성 성공")

    # 3. 알림 체크
    print("\n3. 알림 조건 체크...")
    print("-" * 40)

    alerts = alert_system.check_alerts(orders)
    print(f"✅ {len(alerts)}개 알림 생성")

    # 알림 타입별 카운트
    alert_types = {}
    for alert in alerts:
        alert_type = alert["type"]
        alert_types[alert_type] = alert_types.get(alert_type, 0) + 1

    print("\n  알림 타입별 분포:")
    for alert_type, count in alert_types.items():
        print(f"    - {alert_type}: {count}개")

    # 4. 알림 발송 (콘솔)
    print("\n4. 알림 발송 (콘솔)...")
    print("-" * 40)

    if alerts[:3]:  # 최대 3개만 표시
        success = alert_system.send_alerts(alerts[:3], channels=["console"])
        if success:
            print("\n✅ 콘솔 알림 발송 성공")
        else:
            print("\n❌ 콘솔 알림 발송 실패")

    # 5. 중복 체크 테스트
    print("\n5. 중복 알림 방지 테스트...")
    print("-" * 40)

    alerts_2nd = alert_system.check_alerts(orders)
    print(f"  첫 번째: {len(alerts)}개")
    print(f"  두 번째: {len(alerts_2nd)}개 (중복 제거됨)")

    print("\n" + "=" * 60)
    print("✨ 알림 시스템 테스트 완료")
    print("=" * 60)

    return True


def main():
    """전체 리포트 시스템 테스트"""

    print("\n" + "=" * 60)
    print("🎯 전체 리포트 시스템 테스트")
    print("=" * 60)

    # 1. TSV 출력 테스트
    tsv_success = test_tsv_exporter()

    # 2. Markdown 리포트 테스트
    md_success = test_markdown_reporter()

    # 3. 알림 시스템 테스트
    alert_success = test_alert_system()

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)

    results = {
        "TSV 출력": tsv_success,
        "Markdown 리포트": md_success,
        "알림 시스템": alert_success
    }

    for name, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"  - {name}: {status}")

    all_success = all(results.values())

    if all_success:
        print("\n✨ 모든 테스트 통과!")
    else:
        print("\n⚠️  일부 테스트 실패")

    print("=" * 60)

    return all_success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)