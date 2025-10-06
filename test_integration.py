"""
전체 파이프라인 통합 테스트 (End-to-End)
"""
import json
from pathlib import Path
from datetime import datetime
import time

from src.collector.api_client import MusicowAPIClient
from src.calculator.metrics_engine import MetricsEngine
from src.reporter.tsv_exporter import TSVExporter
from src.reporter.markdown_reporter import MarkdownReporter
from src.reporter.alert_system import AlertSystem
from src.utils.helpers import save_json


def test_full_pipeline():
    """전체 파이프라인 E2E 테스트"""

    print("\n" + "=" * 60)
    print("🚀 전체 파이프라인 통합 테스트 (E2E)")
    print("=" * 60)

    results = {
        "start_time": datetime.now(),
        "phases": {},
        "errors": []
    }

    # Phase 1: 데이터 수집
    print("\n" + "=" * 60)
    print("Phase 1: 데이터 수집")
    print("=" * 60)

    try:
        phase1_start = time.time()

        print("\n1. API 클라이언트 생성...")
        api_client = MusicowAPIClient()
        print("✅ API 클라이언트 생성 성공")

        print("\n2. 데이터 수집...")
        orders = api_client.get_validated_orders()

        if not orders:
            raise Exception("데이터 수집 실패")

        print(f"✅ {len(orders):,}개 주문 데이터 수집 성공")

        # 데이터 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        raw_file = Path("data/raw") / f"integration_test_{timestamp}.json"
        save_json(orders, raw_file)
        print(f"✅ 원본 데이터 저장: {raw_file.name}")

        phase1_time = time.time() - phase1_start
        results["phases"]["collection"] = {
            "status": "success",
            "count": len(orders),
            "time": phase1_time,
            "file": str(raw_file)
        }

        api_client.close()

    except Exception as e:
        print(f"❌ Phase 1 실패: {e}")
        results["phases"]["collection"] = {"status": "failed", "error": str(e)}
        results["errors"].append(f"Phase 1: {e}")
        return results

    # Phase 2: 지표 계산
    print("\n" + "=" * 60)
    print("Phase 2: 지표 계산")
    print("=" * 60)

    try:
        phase2_start = time.time()

        print("\n1. Metrics Engine 생성...")
        engine = MetricsEngine()
        print("✅ Metrics Engine 생성 성공")

        print("\n2. 지표 계산 시작...")
        metrics_orders = engine.calculate_batch_metrics(orders)
        print(f"✅ {len(metrics_orders):,}개 주문 지표 계산 완료")

        # 지표 통계
        premiums = [o.get("premium") for o in metrics_orders if o.get("premium") is not None]
        yields = [o.get("normalized_yield") for o in metrics_orders if o.get("normalized_yield") is not None]

        avg_premium = sum(premiums) / len(premiums) if premiums else 0
        avg_yield = sum(yields) / len(yields) if yields else 0

        print(f"\n  평균 괴리율: {avg_premium:.2f}%")
        print(f"  평균 수익률: {avg_yield:.2f}%")

        # 지표 데이터 저장
        metrics_file = Path("data/processed") / f"integration_test_{timestamp}_metrics.json"
        save_json(metrics_orders, metrics_file)
        print(f"\n✅ 지표 데이터 저장: {metrics_file.name}")

        phase2_time = time.time() - phase2_start
        results["phases"]["calculation"] = {
            "status": "success",
            "count": len(metrics_orders),
            "time": phase2_time,
            "avg_premium": avg_premium,
            "avg_yield": avg_yield,
            "file": str(metrics_file)
        }

    except Exception as e:
        print(f"❌ Phase 2 실패: {e}")
        results["phases"]["calculation"] = {"status": "failed", "error": str(e)}
        results["errors"].append(f"Phase 2: {e}")
        return results

    # Phase 3: 리포트 생성
    print("\n" + "=" * 60)
    print("Phase 3: 리포트 생성")
    print("=" * 60)

    try:
        phase3_start = time.time()

        # 3-1. TSV 출력
        print("\n1. TSV 리포트 생성...")
        tsv_exporter = TSVExporter()

        tsv_file = tsv_exporter.export_to_tsv(
            metrics_orders,
            f"integration_test_{timestamp}.tsv"
        )
        print(f"✅ TSV 파일 생성: {tsv_file.name}")

        # 저평가 Top 10
        undervalued_file = tsv_exporter.export_top_orders(
            metrics_orders,
            sort_by="premium",
            top_n=10,
            ascending=True,
            filename=f"integration_test_{timestamp}_undervalued.tsv"
        )
        print(f"✅ 저평가 Top 10: {undervalued_file.name}")

        # 고수익률 Top 10
        high_yield_file = tsv_exporter.export_top_orders(
            metrics_orders,
            sort_by="yield",
            top_n=10,
            ascending=False,
            filename=f"integration_test_{timestamp}_high_yield.tsv"
        )
        print(f"✅ 고수익률 Top 10: {high_yield_file.name}")

        # 3-2. Markdown 리포트
        print("\n2. Markdown 리포트 생성...")
        md_reporter = MarkdownReporter()

        md_file = md_reporter.generate_daily_report(
            metrics_orders,
            f"integration_test_{timestamp}.md"
        )
        print(f"✅ Markdown 리포트: {md_file.name}")

        phase3_time = time.time() - phase3_start
        results["phases"]["reporting"] = {
            "status": "success",
            "time": phase3_time,
            "files": {
                "tsv": str(tsv_file),
                "undervalued": str(undervalued_file),
                "high_yield": str(high_yield_file),
                "markdown": str(md_file)
            }
        }

    except Exception as e:
        print(f"❌ Phase 3 실패: {e}")
        results["phases"]["reporting"] = {"status": "failed", "error": str(e)}
        results["errors"].append(f"Phase 3: {e}")
        return results

    # Phase 4: 알림 시스템
    print("\n" + "=" * 60)
    print("Phase 4: 알림 시스템")
    print("=" * 60)

    try:
        phase4_start = time.time()

        print("\n1. Alert System 생성...")
        alert_system = AlertSystem()
        print("✅ Alert System 생성 성공")

        print("\n2. 알림 조건 체크...")
        alerts = alert_system.check_alerts(metrics_orders)
        print(f"✅ {len(alerts)}개 알림 생성")

        # 알림 타입별 분포
        alert_types = {}
        for alert in alerts:
            alert_type = alert["type"]
            alert_types[alert_type] = alert_types.get(alert_type, 0) + 1

        print("\n  알림 타입별 분포:")
        for alert_type, count in alert_types.items():
            print(f"    - {alert_type}: {count}개")

        # 알림 발송 (상위 5개만)
        if alerts:
            print("\n3. 알림 발송 (상위 5개)...")
            alert_system.send_alerts(alerts[:5], channels=["console"])
            print("✅ 알림 발송 완료")

        phase4_time = time.time() - phase4_start
        results["phases"]["alerting"] = {
            "status": "success",
            "time": phase4_time,
            "alert_count": len(alerts),
            "alert_types": alert_types
        }

    except Exception as e:
        print(f"❌ Phase 4 실패: {e}")
        results["phases"]["alerting"] = {"status": "failed", "error": str(e)}
        results["errors"].append(f"Phase 4: {e}")
        return results

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 통합 테스트 결과 요약")
    print("=" * 60)

    results["end_time"] = datetime.now()
    total_time = (results["end_time"] - results["start_time"]).total_seconds()
    results["total_time"] = total_time

    print(f"\n총 소요 시간: {total_time:.2f}초")
    print("\nPhase별 결과:")

    for phase_name, phase_data in results["phases"].items():
        status_icon = "✅" if phase_data["status"] == "success" else "❌"
        phase_time = phase_data.get("time", 0)
        print(f"  {status_icon} {phase_name}: {phase_data['status']} ({phase_time:.2f}초)")

    # 성능 지표
    if results["phases"]["collection"]["status"] == "success":
        data_count = results["phases"]["collection"]["count"]
        print(f"\n처리 데이터: {data_count:,}개 주문")

        if results["phases"]["calculation"]["status"] == "success":
            calc_time = results["phases"]["calculation"]["time"]
            throughput = data_count / calc_time if calc_time > 0 else 0
            print(f"처리 속도: {throughput:,.0f}건/초")

    # 에러 확인
    if results["errors"]:
        print("\n⚠️  에러 발생:")
        for error in results["errors"]:
            print(f"  - {error}")
    else:
        print("\n✨ 모든 Phase 성공!")

    # 결과 저장
    result_file = Path("data") / f"integration_test_result_{timestamp}.json"
    save_json(results, result_file, indent=2)
    print(f"\n📄 테스트 결과 저장: {result_file.name}")

    print("\n" + "=" * 60)

    return results


def test_data_quality():
    """데이터 품질 검증 테스트"""

    print("\n" + "=" * 60)
    print("🔍 데이터 품질 검증")
    print("=" * 60)

    # 최신 metrics 파일 찾기
    processed_dir = Path("data/processed")
    json_files = list(processed_dir.glob("integration_test_*_metrics.json"))

    if not json_files:
        print("❌ 테스트 데이터 없음")
        return False

    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
    print(f"\n검증 파일: {latest_file.name}")

    with open(latest_file, 'r', encoding='utf-8') as f:
        orders = json.load(f)

    print(f"총 데이터: {len(orders):,}개")

    # 품질 체크
    checks = {
        "완전성": 0,
        "정확성": 0,
        "일관성": 0
    }

    print("\n품질 검증 항목:")

    # 1. 완전성 체크
    print("\n1. 데이터 완전성")
    required_fields = [
        "order_no", "song_name", "order_price", "recent_price",
        "premium", "normalized_yield", "liquidity_score", "signal"
    ]

    complete_count = 0
    for order in orders:
        if all(field in order and order[field] is not None for field in required_fields):
            complete_count += 1

    completeness = (complete_count / len(orders)) * 100
    checks["완전성"] = completeness
    print(f"  완전한 데이터: {complete_count:,}/{len(orders):,} ({completeness:.1f}%)")

    # 2. 정확성 체크 (괴리율 재계산)
    print("\n2. 계산 정확성")
    accurate_count = 0
    for order in orders:
        order_price = order.get("order_price", 0)
        recent_price = order.get("recent_price", 0)
        premium = order.get("premium")

        if recent_price > 0 and premium is not None:
            expected_premium = ((order_price - recent_price) / recent_price) * 100
            if abs(premium - expected_premium) < 0.01:
                accurate_count += 1

    accuracy = (accurate_count / len(orders)) * 100
    checks["정확성"] = accuracy
    print(f"  정확한 계산: {accurate_count:,}/{len(orders):,} ({accuracy:.1f}%)")

    # 3. 일관성 체크
    print("\n3. 데이터 일관성")
    consistent_count = 0
    for order in orders:
        # 가격이 양수인지
        order_price = order.get("order_price", 0)
        recent_price = order.get("recent_price", 0)

        if order_price > 0 and recent_price > 0:
            consistent_count += 1

    consistency = (consistent_count / len(orders)) * 100
    checks["일관성"] = consistency
    print(f"  일관된 데이터: {consistent_count:,}/{len(orders):,} ({consistency:.1f}%)")

    # 종합 평가
    print("\n" + "-" * 40)
    avg_quality = sum(checks.values()) / len(checks)
    print(f"종합 품질 점수: {avg_quality:.1f}%")

    if avg_quality >= 95:
        print("✅ 우수한 데이터 품질")
        return True
    elif avg_quality >= 90:
        print("✅ 양호한 데이터 품질")
        return True
    else:
        print("⚠️  데이터 품질 개선 필요")
        return False


if __name__ == "__main__":
    # 1. 전체 파이프라인 테스트
    results = test_full_pipeline()

    # 2. 데이터 품질 검증
    quality_ok = test_data_quality()

    # 최종 결과
    print("\n" + "=" * 60)
    print("🎯 최종 결과")
    print("=" * 60)

    all_success = (
        all(p.get("status") == "success" for p in results["phases"].values()) and
        quality_ok
    )

    if all_success:
        print("\n✨ 통합 테스트 100% 통과!")
        print("\n시스템이 프로덕션 배포 준비가 완료되었습니다.")
        exit(0)
    else:
        print("\n⚠️  일부 테스트 실패")
        print("\n상세 내용을 확인하고 수정이 필요합니다.")
        exit(1)