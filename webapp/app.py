"""
Flask 웹 애플리케이션 - 뮤직카우 시장 분석 대시보드
"""
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_cors import CORS

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent

app = Flask(__name__)
CORS(app)


def load_latest_data():
    """최신 처리된 데이터 로드"""
    processed_dir = PROJECT_ROOT / "data" / "processed"

    if not processed_dir.exists():
        return None

    # 최신 metrics 파일 찾기
    json_files = list(processed_dir.glob("*_metrics.json"))

    if not json_files:
        return None

    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)

    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data


def calculate_summary_stats(orders):
    """요약 통계 계산"""
    if not orders:
        return {}

    total_orders = len(orders)
    buy_orders = [o for o in orders if o.get("order_type") == "구매"]
    sell_orders = [o for o in orders if o.get("order_type") == "판매"]
    waiting_orders = [o for o in orders if o.get("order_status") == "대기"]

    premiums = [o.get("premium") for o in orders if o.get("premium") is not None]
    yields = [o.get("normalized_yield") for o in orders if o.get("normalized_yield") is not None]
    liquidity_scores = [o.get("liquidity_score") for o in orders if o.get("liquidity_score") is not None]

    avg_premium = sum(premiums) / len(premiums) if premiums else 0
    avg_yield = sum(yields) / len(yields) if yields else 0
    avg_liquidity = sum(liquidity_scores) / len(liquidity_scores) if liquidity_scores else 0

    # 시그널 분포
    signals = {}
    for order in orders:
        signal = order.get("signal", "알 수 없음")
        signals[signal] = signals.get(signal, 0) + 1

    return {
        "total_orders": total_orders,
        "buy_orders": len(buy_orders),
        "sell_orders": len(sell_orders),
        "waiting_orders": len(waiting_orders),
        "avg_premium": round(avg_premium, 2),
        "avg_yield": round(avg_yield, 2),
        "avg_liquidity": round(avg_liquidity, 1),
        "signals": signals,
        "buy_ratio": round(len(buy_orders) / total_orders * 100, 1) if total_orders > 0 else 0,
        "sell_ratio": round(len(sell_orders) / total_orders * 100, 1) if total_orders > 0 else 0,
    }


@app.route('/')
def index():
    """메인 대시보드 페이지"""
    return render_template('index.html')


@app.route('/api/summary')
def api_summary():
    """요약 통계 API"""
    orders = load_latest_data()

    if not orders:
        return jsonify({
            "error": "데이터를 찾을 수 없습니다",
            "timestamp": datetime.now().isoformat()
        }), 404

    stats = calculate_summary_stats(orders)
    stats["timestamp"] = datetime.now().isoformat()
    stats["data_count"] = len(orders)

    return jsonify(stats)


@app.route('/api/top-yield')
def api_top_yield():
    """고수익률 주문 API (Top 10)"""
    orders = load_latest_data()

    if not orders:
        return jsonify({"error": "데이터를 찾을 수 없습니다"}), 404

    # 구매 주문만 필터링하고 수익률 기준 정렬
    buy_orders = [o for o in orders if o.get("order_type") == "구매"]
    sorted_orders = sorted(
        buy_orders,
        key=lambda x: x.get("normalized_yield", 0),
        reverse=True
    )[:10]

    return jsonify(sorted_orders)


@app.route('/api/undervalued')
def api_undervalued():
    """저평가 주문 API (Top 10)"""
    orders = load_latest_data()

    if not orders:
        return jsonify({"error": "데이터를 찾을 수 없습니다"}), 404

    # 구매 주문만 필터링하고 프리미엄율 기준 정렬 (낮은 순)
    buy_orders = [o for o in orders if o.get("order_type") == "구매"]
    sorted_orders = sorted(
        buy_orders,
        key=lambda x: x.get("premium", 0)
    )[:10]

    return jsonify(sorted_orders)


@app.route('/api/high-liquidity')
def api_high_liquidity():
    """고유동성 주문 API (Top 10)"""
    orders = load_latest_data()

    if not orders:
        return jsonify({"error": "데이터를 찾을 수 없습니다"}), 404

    sorted_orders = sorted(
        orders,
        key=lambda x: x.get("liquidity_score", 0),
        reverse=True
    )[:10]

    return jsonify(sorted_orders)


@app.route('/api/signals')
def api_signals():
    """시그널 분포 API"""
    orders = load_latest_data()

    if not orders:
        return jsonify({"error": "데이터를 찾을 수 없습니다"}), 404

    signals = {}
    for order in orders:
        signal = order.get("signal", "알 수 없음")
        signals[signal] = signals.get(signal, 0) + 1

    # 비율 계산
    total = sum(signals.values())
    signal_data = [
        {
            "signal": signal,
            "count": count,
            "percentage": round(count / total * 100, 1) if total > 0 else 0
        }
        for signal, count in sorted(signals.items(), key=lambda x: x[1], reverse=True)
    ]

    return jsonify(signal_data)


@app.route('/api/premium-distribution')
def api_premium_distribution():
    """프리미엄율 분포 API"""
    orders = load_latest_data()

    if not orders:
        return jsonify({"error": "데이터를 찾을 수 없습니다"}), 404

    # 프리미엄율 구간별 분포
    ranges = {
        "매우 저평가 (< -20%)": 0,
        "저평가 (-20% ~ -10%)": 0,
        "적정 (-10% ~ 10%)": 0,
        "고평가 (10% ~ 20%)": 0,
        "매우 고평가 (> 20%)": 0,
    }

    for order in orders:
        premium = order.get("premium")
        if premium is None:
            continue

        if premium < -20:
            ranges["매우 저평가 (< -20%)"] += 1
        elif premium < -10:
            ranges["저평가 (-20% ~ -10%)"] += 1
        elif premium <= 10:
            ranges["적정 (-10% ~ 10%)"] += 1
        elif premium <= 20:
            ranges["고평가 (10% ~ 20%)"] += 1
        else:
            ranges["매우 고평가 (> 20%)"] += 1

    distribution_data = [
        {"range": range_name, "count": count}
        for range_name, count in ranges.items()
    ]

    return jsonify(distribution_data)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
