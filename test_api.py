"""
API 클라이언트 테스트
"""
from src.collector.api_client import MusicowAPIClient
import json


def test_api_client():
    """API 클라이언트 테스트"""

    print("\n" + "=" * 60)
    print("🎵 뮤직카우 API 클라이언트 테스트")
    print("=" * 60)

    # 클라이언트 생성
    client = MusicowAPIClient()

    # 1. 연결 테스트
    print("\n1. API 연결 테스트...")
    print("-" * 40)
    if client.test_connection():
        print("✅ API 연결 성공")
    else:
        print("❌ API 연결 실패")
        client.close()
        return False

    # 2. 데이터 가져오기 테스트
    print("\n2. 데이터 가져오기 테스트...")
    print("-" * 40)
    orders = client.get_validated_orders()

    if orders:
        print(f"✅ {len(orders)}개 주문 데이터 수신")

        # 첫 번째 주문 데이터 샘플 출력
        if orders:
            print("\n3. 샘플 데이터 (첫 번째 주문):")
            print("-" * 40)
            sample = orders[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")

        # 데이터 통계
        print("\n4. 데이터 통계:")
        print("-" * 40)

        # 주문 타입별 카운트
        buy_count = sum(1 for o in orders if o.get("order_type") == "구매")
        sell_count = sum(1 for o in orders if o.get("order_type") == "판매")
        print(f"  구매 주문: {buy_count}개")
        print(f"  판매 주문: {sell_count}개")

        # 주문 상태별 카운트
        status_counts = {}
        for order in orders:
            status = order.get("order_status", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        print(f"\n  주문 상태:")
        for status, count in status_counts.items():
            print(f"    - {status}: {count}개")

        # 상위 5개 곡
        song_counts = {}
        for order in orders:
            song = order.get("song_name", "Unknown")
            song_counts[song] = song_counts.get(song, 0) + 1

        print(f"\n  상위 거래 곡 (Top 5):")
        top_songs = sorted(song_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (song, count) in enumerate(top_songs, 1):
            print(f"    {i}. {song}: {count}개 주문")

        # 샘플 데이터 저장
        print("\n5. 샘플 데이터 저장...")
        print("-" * 40)
        sample_file = "data/raw/sample_orders.json"
        try:
            with open(sample_file, 'w', encoding='utf-8') as f:
                json.dump(orders[:10], f, ensure_ascii=False, indent=2)
            print(f"✅ 샘플 데이터 저장 완료: {sample_file}")
        except Exception as e:
            print(f"❌ 샘플 데이터 저장 실패: {e}")

    else:
        print("❌ 데이터 가져오기 실패")
        client.close()
        return False

    # 클라이언트 종료
    client.close()

    print("\n" + "=" * 60)
    print("✨ API 클라이언트 테스트 완료")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = test_api_client()
    exit(0 if success else 1)