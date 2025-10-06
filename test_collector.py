"""
데이터 수집기 테스트
"""
import os
import json
from pathlib import Path
from datetime import datetime
from src.collector.data_collector import DataCollector


def test_collector():
    """데이터 수집기 테스트"""

    print("\n" + "=" * 60)
    print("📊 데이터 수집기 테스트")
    print("=" * 60)

    # 수집기 생성
    collector = DataCollector()

    # 1. 1회 수집 테스트
    print("\n1. 데이터 수집 테스트...")
    print("-" * 40)

    if collector.collect_once():
        print("✅ 데이터 수집 성공")

        # 저장된 파일 확인
        today = datetime.now().strftime("%Y%m%d")
        today_dir = Path("data/raw") / today

        if today_dir.exists():
            files = list(today_dir.glob("*_orders.json"))
            print(f"\n2. 저장된 파일 확인:")
            print("-" * 40)
            print(f"  디렉토리: {today_dir}")
            print(f"  파일 개수: {len(files)}개")

            if files:
                # 최신 파일 확인
                latest_file = max(files, key=lambda f: f.stat().st_mtime)
                print(f"  최신 파일: {latest_file.name}")

                # 파일 내용 확인
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"  데이터 개수: {len(data)}개")

                    # 간단한 통계
                    if data:
                        print("\n3. 데이터 통계:")
                        print("-" * 40)

                        buy_count = sum(1 for o in data if o.get("order_type") == "구매")
                        sell_count = sum(1 for o in data if o.get("order_type") == "판매")
                        print(f"  구매 주문: {buy_count}개")
                        print(f"  판매 주문: {sell_count}개")

                        # 주문 상태
                        status_counts = {}
                        for order in data:
                            status = order.get("order_status", "Unknown")
                            status_counts[status] = status_counts.get(status, 0) + 1

                        print(f"\n  주문 상태:")
                        for status, count in status_counts.items():
                            print(f"    - {status}: {count}개")

                        # 파일 크기
                        file_size = latest_file.stat().st_size
                        print(f"\n  파일 크기: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        else:
            print(f"❌ 디렉토리 없음: {today_dir}")

    else:
        print("❌ 데이터 수집 실패")
        return False

    print("\n" + "=" * 60)
    print("✨ 데이터 수집기 테스트 완료")
    print("=" * 60)

    return True


def test_scheduler():
    """스케줄러 테스트 (짧은 시간)"""

    print("\n" + "=" * 60)
    print("⏰ 스케줄러 테스트 (30초 실행)")
    print("=" * 60)

    import time
    import threading

    collector = DataCollector()

    # 별도 스레드에서 스케줄러 실행
    def run_scheduler():
        # 테스트용으로 1분 간격 설정
        import schedule
        schedule.every(10).seconds.do(collector.collect_data)

        for _ in range(3):  # 30초 동안만 실행
            schedule.run_pending()
            time.sleep(10)

        collector.stop_scheduler()

    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()

    print("스케줄러 실행 중... (30초간)")
    scheduler_thread.join()

    print("\n✅ 스케줄러 테스트 완료")


if __name__ == "__main__":
    # 기본 수집 테스트
    success = test_collector()

    # 스케줄러 테스트는 선택사항
    # 주석 해제하여 실행 가능
    # if success:
    #     test_scheduler()

    exit(0 if success else 1)