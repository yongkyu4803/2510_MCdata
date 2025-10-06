"""
패키지 import 테스트
"""

def test_imports():
    """필수 패키지 import 테스트"""

    print("📦 패키지 Import 테스트 시작...")
    print("-" * 50)

    packages = [
        ("pandas", "pd"),
        ("requests", None),
        ("schedule", None),
        ("dotenv", None),
        ("json", None),
        ("datetime", None),
        ("pathlib", None)
    ]

    success_count = 0
    total_count = len(packages)

    for package, alias in packages:
        try:
            if alias:
                exec(f"import {package} as {alias}")
                print(f"✅ {package} (as {alias}) - Success")
            else:
                exec(f"import {package}")
                print(f"✅ {package} - Success")
            success_count += 1
        except ImportError as e:
            print(f"❌ {package} - Failed: {e}")

    print("-" * 50)

    # 프로젝트 모듈 import 테스트
    print("\n📁 프로젝트 모듈 테스트...")
    print("-" * 50)

    try:
        from config.settings import MUSICOW_API_URL, BASE_DIR
        print(f"✅ config.settings - Success")
        print(f"   - API URL: {MUSICOW_API_URL}")
        print(f"   - BASE DIR: {BASE_DIR}")
        success_count += 1
        total_count += 1
    except ImportError as e:
        print(f"❌ config.settings - Failed: {e}")
        total_count += 1

    try:
        from src.utils.logger import setup_logger
        logger = setup_logger("test")
        print(f"✅ src.utils.logger - Success")
        logger.info("Test log message")
        success_count += 1
        total_count += 1
    except ImportError as e:
        print(f"❌ src.utils.logger - Failed: {e}")
        total_count += 1

    try:
        from src.utils.validators import DataValidator
        print(f"✅ src.utils.validators - Success")
        success_count += 1
        total_count += 1
    except ImportError as e:
        print(f"❌ src.utils.validators - Failed: {e}")
        total_count += 1

    try:
        from src.utils.helpers import get_timestamp, save_json
        print(f"✅ src.utils.helpers - Success")
        success_count += 1
        total_count += 1
    except ImportError as e:
        print(f"❌ src.utils.helpers - Failed: {e}")
        total_count += 1

    print("-" * 50)
    print(f"\n📊 결과: {success_count}/{total_count} 성공")

    if success_count == total_count:
        print("✨ 모든 패키지 및 모듈 import 성공!")
        return True
    else:
        print(f"⚠️  일부 import 실패 ({total_count - success_count}개)")
        return False


if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)