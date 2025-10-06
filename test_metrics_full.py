"""
전체 데이터로 지표 계산 엔진 테스트
"""
import json
from pathlib import Path
from datetime import datetime
from src.calculator.metrics_engine import MetricsEngine
from src.utils.helpers import save_json


def test_full_dataset():
    """전체 데이터셋으로 테스트"""

    print("\n" + "=" * 60)
    print("📊 전체 데이터 지표 계산 테스트")
    print("=" * 60)

    # 1. 최신 데이터 파일 찾기
    print("\n1. 데이터 파일 찾기...")
    print("-" * 40)

    today = datetime.now().strftime("%Y%m%d")
    data_dir = Path("data/raw") / today

    if not data_dir.exists():
        print(f"❌ 데이터 디렉토리 없음: {data_dir}")
        return False

    # 최신 파일 찾기
    json_files = list(data_dir.glob("*_orders.json"))
    if not json_files:
        print(f"❌ JSON 파일 없음")
        return False

    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
    print(f"✅ 최신 파일: {latest_file.name}")

    # 2. 데이터 로드
    print("\n2. 데이터 로드...")
    print("-" * 40)

    with open(latest_file, 'r', encoding='utf-8') as f:
        orders = json.load(f)

    print(f"✅ {len(orders):,}개 주문 데이터 로드")

    # 3. 지표 계산
    print("\n3. 지표 계산 시작...")
    print("-" * 40)

    engine = MetricsEngine()
    start_time = datetime.now()

    results = engine.calculate_batch_metrics(orders)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"✅ 계산 완료: {len(results):,}개")
    print(f"  소요 시간: {duration:.2f}초")
    print(f"  처리 속도: {len(results)/duration:.0f}건/초")

    # 4. 통계 분석
    print("\n4. 통계 분석...")
    print("-" * 40)

    # 시그널 분포
    signal_counts = {}
    for r in results:
        signal = r.get("signal", "Unknown")
        signal_counts[signal] = signal_counts.get(signal, 0) + 1

    print("\n[시그널 분포]")
    for signal, count in sorted(signal_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(results) * 100
        print(f"  {signal:20} : {count:4}개 ({percentage:5.1f}%)")

    # 괴리율 분석
    premiums = [r.get("premium") for r in results if r.get("premium") is not None]
    if premiums:
        print("\n[괴리율 통계]")
        print(f"  평균: {sum(premiums)/len(premiums):>7.2f}%")
        print(f"  최대: {max(premiums):>7.2f}%")
        print(f"  최소: {min(premiums):>7.2f}%")

        # 분포
        high = len([p for p in premiums if p > 10])
        low = len([p for p in premiums if p < -10])
        normal = len(premiums) - high - low
        print(f"  고평가 (>10%): {high}개 ({high/len(premiums)*100:.1f}%)")
        print(f"  저평가 (<-10%): {low}개 ({low/len(premiums)*100:.1f}%)")
        print(f"  정상 범위: {normal}개 ({normal/len(premiums)*100:.1f}%)")

    # 정규화 수익률 분석
    yields = [r.get("normalized_yield") for r in results if r.get("normalized_yield") is not None]
    if yields:
        print("\n[정규화 수익률 통계]")
        print(f"  평균: {sum(yields)/len(yields):>7.2f}%")
        print(f"  최대: {max(yields):>7.2f}%")
        print(f"  최소: {min(yields):>7.2f}%")

    # 유동성 분석
    liquidity_scores = [r.get("liquidity_score", 0) for r in results]
    print("\n[유동성 점수 통계]")
    print(f"  평균: {sum(liquidity_scores)/len(liquidity_scores):>7.1f}/100")
    print(f"  최대: {max(liquidity_scores):>7.1f}/100")
    print(f"  최소: {min(liquidity_scores):>7.1f}/100")

    high_liq = len([s for s in liquidity_scores if s > 80])
    low_liq = len([s for s in liquidity_scores if s < 30])
    print(f"  높은 유동성 (>80): {high_liq}개 ({high_liq/len(liquidity_scores)*100:.1f}%)")
    print(f"  낮은 유동성 (<30): {low_liq}개 ({low_liq/len(liquidity_scores)*100:.1f}%)")

    # 5. 주요 주문 출력
    print("\n5. 주요 주문 분석...")
    print("-" * 40)

    # 저평가 주문 (괴리율 낮은 순)
    print("\n[저평가 주문 Top 10]")
    low_premium = sorted(
        [r for r in results if r.get("premium") is not None and r.get("order_status") == "대기"],
        key=lambda x: x.get("premium", 0)
    )[:10]

    for i, order in enumerate(low_premium, 1):
        print(f"{i:2}. {order['song_name'][:25]:25} | "
              f"{order['song_artist'][:15]:15} | "
              f"괴리: {order['premium']:>6.2f}% | "
              f"수익률: {order['normalized_yield']:>5.2f}% | "
              f"유동성: {order['liquidity_score']:>4.1f}")

    # 고수익률 주문
    print("\n[고수익률 주문 Top 10]")
    high_yield = sorted(
        [r for r in results if r.get("normalized_yield") is not None and r.get("order_status") == "대기"],
        key=lambda x: x.get("normalized_yield", 0),
        reverse=True
    )[:10]

    for i, order in enumerate(high_yield, 1):
        print(f"{i:2}. {order['song_name'][:25]:25} | "
              f"{order['song_artist'][:15]:15} | "
              f"수익률: {order['normalized_yield']:>5.2f}% | "
              f"괴리: {order['premium']:>6.2f}% | "
              f"유동성: {order['liquidity_score']:>4.1f}")

    # 고유동성 주문
    print("\n[고유동성 주문 Top 10]")
    high_liquidity = sorted(
        results,
        key=lambda x: x.get("liquidity_score", 0),
        reverse=True
    )[:10]

    for i, order in enumerate(high_liquidity, 1):
        print(f"{i:2}. {order['song_name'][:25]:25} | "
              f"{order['song_artist'][:15]:15} | "
              f"유동성: {order['liquidity_score']:>4.1f} | "
              f"괴리: {order['premium']:>6.2f}% | "
              f"시그널: {order['signal']}")

    # 6. 결과 저장
    print("\n6. 결과 저장...")
    print("-" * 40)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = Path("data/processed") / f"{timestamp}_metrics.json"

    if save_json(results, output_file):
        file_size = output_file.stat().st_size
        print(f"✅ 결과 저장: {output_file.name}")
        print(f"  파일 크기: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
    else:
        print("❌ 결과 저장 실패")

    print("\n" + "=" * 60)
    print("✨ 전체 데이터 지표 계산 완료")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = test_full_dataset()
    exit(0 if success else 1)