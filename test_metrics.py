"""
지표 계산 엔진 테스트
"""
import json
from pathlib import Path
from src.calculator.metrics_engine import MetricsEngine
from src.utils.helpers import save_json


def test_metrics_engine():
    """지표 계산 엔진 테스트"""

    print("\n" + "=" * 60)
    print("📊 지표 계산 엔진 테스트")
    print("=" * 60)

    # 1. 지표 계산기 생성
    print("\n1. 지표 계산기 생성...")
    print("-" * 40)
    engine = MetricsEngine()
    print("✅ MetricsEngine 생성 성공")

    # 2. 샘플 데이터 로드
    print("\n2. 샘플 데이터 로드...")
    print("-" * 40)

    sample_file = Path("data/raw/sample_orders.json")
    if not sample_file.exists():
        print(f"❌ 샘플 파일 없음: {sample_file}")
        print("먼저 test_api.py를 실행하여 샘플 데이터를 생성하세요.")
        return False

    with open(sample_file, 'r', encoding='utf-8') as f:
        orders = json.load(f)

    print(f"✅ {len(orders)}개 주문 데이터 로드")

    # 3. 기본 지표 계산 테스트
    print("\n3. 기본 지표 계산 테스트...")
    print("-" * 40)

    sample_order = orders[0]
    print(f"테스트 주문: {sample_order['song_name']}")
    print(f"  - 주문 가격: {sample_order['order_price']:,}원")
    print(f"  - 최근 가격: {sample_order['recent_price']:,}원")
    print(f"  - 수익률: {sample_order['order_royalty_rate']*100:.1f}%")

    # 괴리율 계산
    premium = engine.calculate_premium(
        sample_order['order_price'],
        sample_order['recent_price']
    )
    print(f"\n  괴리율: {premium:.2f}%")

    # 정규화 수익률 계산
    normalized_yield = engine.calculate_normalized_yield(
        sample_order['order_royalty_rate'],
        sample_order['order_price']
    )
    print(f"  정규화 수익률: {normalized_yield:.2f}%")

    # 유동성 점수 계산
    liquidity_score = engine.calculate_liquidity_score(
        orders,
        sample_order['song_name']
    )
    print(f"  유동성 점수: {liquidity_score:.1f}/100")

    # 시그널 생성
    signal = engine.generate_signal(premium, liquidity_score)
    print(f"  시그널: {signal}")

    # 4. 배치 계산 테스트
    print("\n4. 배치 지표 계산 테스트...")
    print("-" * 40)

    results = engine.calculate_batch_metrics(orders)
    print(f"✅ {len(results)}개 주문 지표 계산 완료")

    # 5. 결과 분석
    print("\n5. 계산 결과 분석...")
    print("-" * 40)

    # 시그널별 카운트
    signal_counts = {}
    for r in results:
        signal = r.get("signal", "Unknown")
        signal_counts[signal] = signal_counts.get(signal, 0) + 1

    print("시그널 분포:")
    for signal, count in sorted(signal_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {signal}: {count}개 ({count/len(results)*100:.1f}%)")

    # 괴리율 통계
    premiums = [r.get("premium") for r in results if r.get("premium") is not None]
    if premiums:
        avg_premium = sum(premiums) / len(premiums)
        max_premium = max(premiums)
        min_premium = min(premiums)
        print(f"\n괴리율 통계:")
        print(f"  - 평균: {avg_premium:.2f}%")
        print(f"  - 최대: {max_premium:.2f}%")
        print(f"  - 최소: {min_premium:.2f}%")

    # 유동성 점수 통계
    liquidity_scores = [r.get("liquidity_score", 0) for r in results]
    avg_liquidity = sum(liquidity_scores) / len(liquidity_scores)
    print(f"\n유동성 점수:")
    print(f"  - 평균: {avg_liquidity:.1f}/100")

    # 6. 결과 저장
    print("\n6. 계산 결과 저장...")
    print("-" * 40)

    output_file = Path("data/processed/sample_metrics.json")
    if save_json(results, output_file):
        print(f"✅ 결과 저장 완료: {output_file}")

        # 파일 크기 확인
        file_size = output_file.stat().st_size
        print(f"  파일 크기: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    else:
        print(f"❌ 결과 저장 실패")

    # 7. 상위/하위 주문 출력
    print("\n7. 주요 주문 (상위 5개):")
    print("-" * 40)

    # 괴리율 기준 정렬
    sorted_by_premium = sorted(
        [r for r in results if r.get("premium") is not None],
        key=lambda x: x.get("premium", 0),
        reverse=True
    )

    print("\n[괴리율 상위 5개 - 고평가]")
    for i, order in enumerate(sorted_by_premium[:5], 1):
        print(f"{i}. {order['song_name'][:20]:20} | "
              f"괴리율: {order['premium']:>6.2f}% | "
              f"유동성: {order['liquidity_score']:>4.1f} | "
              f"시그널: {order['signal']}")

    print("\n[괴리율 하위 5개 - 저평가]")
    for i, order in enumerate(sorted_by_premium[-5:], 1):
        print(f"{i}. {order['song_name'][:20]:20} | "
              f"괴리율: {order['premium']:>6.2f}% | "
              f"유동성: {order['liquidity_score']:>4.1f} | "
              f"시그널: {order['signal']}")

    print("\n" + "=" * 60)
    print("✨ 지표 계산 엔진 테스트 완료")
    print("=" * 60)

    return True


def test_individual_metrics():
    """개별 지표 계산 테스트"""

    print("\n" + "=" * 60)
    print("🧪 개별 지표 계산 테스트")
    print("=" * 60)

    engine = MetricsEngine()

    # 테스트 케이스들
    test_cases = [
        {
            "name": "정상 케이스",
            "order_price": 15000,
            "recent_price": 13000,
            "royalty_rate": 0.08,
            "expected_premium": 15.38,
            "expected_yield": 5.33
        },
        {
            "name": "저평가 케이스",
            "order_price": 10000,
            "recent_price": 13000,
            "royalty_rate": 0.08,
            "expected_premium": -23.08,
            "expected_yield": 8.0
        },
        {
            "name": "고평가 케이스",
            "order_price": 20000,
            "recent_price": 15000,
            "royalty_rate": 0.08,
            "expected_premium": 33.33,
            "expected_yield": 4.0
        },
    ]

    print("\n괴리율 및 정규화 수익률 계산 테스트:")
    print("-" * 60)

    for i, case in enumerate(test_cases, 1):
        print(f"\n테스트 {i}: {case['name']}")

        premium = engine.calculate_premium(case['order_price'], case['recent_price'])
        normalized_yield = engine.calculate_normalized_yield(
            case['royalty_rate'],
            case['order_price']
        )

        print(f"  주문가: {case['order_price']:,}원, 최근가: {case['recent_price']:,}원")
        print(f"  괴리율: {premium:.2f}% (예상: {case['expected_premium']:.2f}%)")
        print(f"  정규화 수익률: {normalized_yield:.2f}% (예상: {case['expected_yield']:.2f}%)")

        # 검증
        if abs(premium - case['expected_premium']) < 0.1:
            print(f"  ✅ 괴리율 계산 정확")
        else:
            print(f"  ❌ 괴리율 계산 오차 발생")

        if abs(normalized_yield - case['expected_yield']) < 0.1:
            print(f"  ✅ 정규화 수익률 계산 정확")
        else:
            print(f"  ❌ 정규화 수익률 계산 오차 발생")

    # 시그널 생성 테스트
    print("\n\n시그널 생성 테스트:")
    print("-" * 60)

    signal_test_cases = [
        {"premium": -15, "liquidity": 60, "expected": "저평가"},
        {"premium": 15, "liquidity": 60, "expected": "고평가"},
        {"premium": 5, "liquidity": 85, "expected": "유동성↑"},
        {"premium": 5, "liquidity": 25, "expected": "유동성↓"},
        {"premium": 15, "liquidity": 25, "expected": "주의"},
        {"premium": 5, "liquidity": 50, "expected": "보통"},
    ]

    for i, case in enumerate(signal_test_cases, 1):
        signal = engine.generate_signal(case["premium"], case["liquidity"])
        status = "✅" if signal == case["expected"] else "❌"
        print(f"{i}. 괴리율: {case['premium']:>6.1f}%, 유동성: {case['liquidity']:>4.1f} "
              f"→ {signal:10} (예상: {case['expected']:10}) {status}")

    print("\n" + "=" * 60)
    print("✨ 개별 지표 테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    # 개별 지표 테스트
    test_individual_metrics()

    # 전체 엔진 테스트
    success = test_metrics_engine()

    exit(0 if success else 1)