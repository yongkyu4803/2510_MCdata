"""
Streamlit 대시보드 - 뮤직카우 시장 분석
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta, timezone
import json

# 페이지 설정
st.set_page_config(
    page_title="🎵 뮤직카우 시장 분석",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent

# KST 타임존 설정
KST = timezone(timedelta(hours=9))

def get_kst_now():
    """현재 KST 시간 반환"""
    return datetime.now(KST)


@st.cache_data(ttl=300)  # 5분 캐시
def load_latest_data():
    """뮤직카우 API에서 최신 데이터 수집 및 지표 계산"""
    try:
        import requests
        from src.calculator.metrics_engine import MetricsEngine

        # 뮤직카우 API에서 데이터 가져오기
        api_url = "https://data.musicow.com/files/v1/market/orders.json"
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()

        raw_data = response.json()

        if not raw_data:
            return None

        # 지표 계산 (배치 처리)
        engine = MetricsEngine()
        metrics_data = engine.calculate_batch_metrics(raw_data)

        if not metrics_data:
            return None

        # DataFrame 변환
        df = pd.DataFrame(metrics_data)

        if 'order_date' in df.columns:
            df['order_date'] = pd.to_datetime(df['order_date'])

        return df

    except requests.exceptions.RequestException as e:
        st.error(f"API 연결 오류: {str(e)}")
        return None
    except Exception as e:
        st.error(f"데이터 처리 중 오류 발생: {str(e)}")
        return None


def calculate_summary_stats(df):
    """요약 통계 계산"""
    if df is None or df.empty:
        return {}

    total_orders = len(df)
    buy_orders = len(df[df['order_type'] == '구매'])
    sell_orders = len(df[df['order_type'] == '판매'])
    waiting_orders = len(df[df['order_status'] == '대기'])

    avg_spread = df['spread_rate'].mean()
    avg_yield = df['expected_yield'].mean()
    avg_liquidity = df['liquidity_score'].mean()

    # 시그널 분포
    signals = df['signal'].value_counts().to_dict()

    return {
        "total_orders": total_orders,
        "buy_orders": buy_orders,
        "sell_orders": sell_orders,
        "waiting_orders": waiting_orders,
        "avg_spread": avg_spread,
        "avg_yield": avg_yield,
        "avg_liquidity": avg_liquidity,
        "signals": signals,
        "buy_ratio": buy_orders / total_orders * 100 if total_orders > 0 else 0,
        "sell_ratio": sell_orders / total_orders * 100 if total_orders > 0 else 0,
    }


def main():
    # 헤더
    st.title("🎵 뮤직카우 시장 분석 대시보드")
    st.markdown("실시간 음악 저작권 거래 데이터 분석")

    # 지표 가이드 링크
    with st.expander("📚 지표 이해 가이드 (클릭하여 펼치기)"):
        st.markdown("""
        ### 🎯 핵심 지표 3가지

        #### 1. 스프레드율 (Spread Rate)
        - **정의**: 주문가가 최근가 대비 얼마나 차이 나는지
        - **계산**: `(주문가 - 최근가) / 최근가 × 100`
        - **음수(-)**: 저평가 (주문가 < 최근가)
        - **양수(+)**: 고평가 (주문가 > 최근가)
        - **추천**: -20% ~ -10% (적당한 저평가)

        #### 2. 예상 수익률 (Expected Yield)
        - **정의**: 투자금 대비 예상 연간 수익률
        - **계산**: `(저작권료율 × 기준단가) / 주문가 × 100`
        - **10% 이상**: 고수익률 (우수)
        - **5~10%**: 보통 수익률 (양호)
        - **추천**: 7~12% (안정적 수익)

        **💡 기준단가란?**
        - 저작권료 지급의 기준이 되는 단가
        - 1개 조각당 1년간 받을 예상 저작권료 계산 기준
        - 예시: 기준단가 10,000원 × 저작권료율 8% = 연간 800원 수익

        #### 3. 유동성 점수 (Liquidity Score)
        - **정의**: 얼마나 쉽게 사고팔 수 있는지 (0~100점)
        - **구성**: 스프레드(40%) + 깊이(30%) + 빈도(30%)
        - **80~100점**: 초고유동성 (즉시 거래)
        - **60~80점**: 고유동성 (빠른 거래)
        - **40~60점**: 중유동성 (거래 가능)
        - **추천**: 40점 이상

        ---

        ### 🎯 시그널 해석

        - **저평가**: 싸고 거래 활발 → 적극 매수 검토
        - **저평가, 유동성↓**: 싸지만 팔기 어려움 → 장기 투자
        - **고평가**: 비싸고 거래 활발 → 매도 검토
        - **유동성↑**: 거래 매우 활발 → 단기 투자 적합
        - **유동성↓**: 거래 어려움 → 비추천
        - **주의**: 비싸고 팔기 어려움 → 투자 금지
        - **보통**: 특별한 특징 없음 → 중립

        ---

        ### 💡 투자 체크리스트

        ✅ **매수 전 확인**
        - [ ] 스프레드율 -10% 이하
        - [ ] 수익률 5% 이상
        - [ ] 유동성 30점 이상
        - [ ] 시그널이 "주의" 아님

        ⚠️ **주의사항**
        - 베타 서비스 데이터 (불일치 가능)
        - 최근가는 과거 데이터일 수 있음
        - 저작권료는 과거 실적 기반
        - 모든 투자 판단은 본인 책임

        📄 **상세 가이드**: [METRICS_GUIDE.md](https://github.com/your-repo/METRICS_GUIDE.md) 참고
        """)

    st.markdown("---")

    # 데이터 로드
    with st.spinner("🔄 뮤직카우 API에서 최신 데이터 수집 중... (최대 30초 소요)"):
        df = load_latest_data()

    if df is None or df.empty:
        st.error("⚠️ 데이터를 수집할 수 없습니다. API 연결을 확인해주세요.")
        st.info("""
        **문제 해결**:
        - 뮤직카우 API가 일시적으로 응답하지 않을 수 있습니다.
        - 잠시 후 페이지를 새로고침해주세요.
        - 문제가 지속되면 [뮤직카우 사이트](https://www.musicow.com)를 확인해주세요.
        """)
        return

    # 데이터 수집 완료 메시지
    st.success(f"✅ 최신 데이터 {len(df):,}건 수집 완료!")

    # 필터 적용 여부 선택
    use_filter = st.sidebar.checkbox("🔍 필터 사용", value=False)

    # 기본값 설정
    all_order_types = sorted(df['order_type'].unique().tolist()) if 'order_type' in df.columns else []
    all_signals = sorted(df['signal'].unique().tolist()) if 'signal' in df.columns else []

    # 스프레드율 범위 기본값 (계산된 데이터가 있는 경우만)
    if 'spread_rate' in df.columns:
        spread_min = float(df['spread_rate'].min())
        spread_max = float(df['spread_rate'].max())
    else:
        spread_min = -50.0
        spread_max = 50.0

    # 사이드바
    if use_filter:
        with st.sidebar:
            st.markdown("---")
            st.header("📊 필터 옵션")

            # 주문 타입 필터
            order_types = st.multiselect(
                "주문 타입",
                options=all_order_types,
                default=all_order_types
            )

            # 시그널 필터
            signals = st.multiselect(
                "시그널",
                options=all_signals,
                default=all_signals
            )

            # 스프레드율 범위
            spread_range = st.slider(
                "스프레드율 범위 (%)",
                min_value=spread_min,
                max_value=spread_max,
                value=(spread_min, spread_max),
                step=1.0
            )

            st.markdown("---")
            st.subheader("📦 대량 주문 필터")

            # 대량 주문 필터 활성화
            enable_bulk_filter = st.checkbox("대량 주문만 보기", value=False)

            if enable_bulk_filter:
                # 곡별 대량 주문 기준 (동일 곡에 대한 대기 주문 수)
                bulk_threshold = st.slider(
                    "최소 주문 수 (곡별)",
                    min_value=3,
                    max_value=20,
                    value=10,
                    step=1,
                    help="동일 곡에 대한 대기 주문이 이 수치 이상인 경우 대량 주문으로 간주"
                )
    else:
        # 필터 미사용 시 전체 데이터 사용
        order_types = all_order_types
        signals = all_signals
        spread_range = (spread_min, spread_max)
        enable_bulk_filter = False
        bulk_threshold = 10

    with st.sidebar:
        st.markdown("---")
        st.info(f"📅 마지막 업데이트 (KST)\n\n{get_kst_now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 필터 적용
    filtered_df = df[
        (df['order_type'].isin(order_types)) &
        (df['signal'].isin(signals)) &
        (df['spread_rate'] >= spread_range[0]) &
        (df['spread_rate'] <= spread_range[1])
    ].copy()  # 복사본 생성으로 경고 방지

    # 대량 주문 필터 적용
    if enable_bulk_filter:
        # 곡별 주문 수 계산 (대기 중인 주문만)
        waiting_df = filtered_df[filtered_df['order_status'] == '대기']
        song_counts = waiting_df['song_name'].value_counts()

        # 임계값 이상인 곡만 선택
        bulk_songs = song_counts[song_counts >= bulk_threshold].index.tolist()

        # 대량 주문 곡만 필터링
        filtered_df = filtered_df[filtered_df['song_name'].isin(bulk_songs)].copy()

        # 대량 주문 정보 추가
        filtered_df['order_count'] = filtered_df['song_name'].map(song_counts).fillna(0).astype(int)
    else:
        # 필터 미사용 시 변수 초기화
        bulk_songs = []
        song_counts = pd.Series(dtype=int)

    # 사이드바에 필터링 결과 표시
    with st.sidebar:
        st.markdown("---")
        st.metric(
            label="📊 필터링 결과",
            value=f"{len(filtered_df):,}개",
            delta=f"{len(filtered_df)/len(df)*100:.1f}%" if len(df) > 0 else "0%"
        )

        if enable_bulk_filter:
            st.metric(
                label="📦 대량 주문 곡 수",
                value=f"{len(bulk_songs)}곡",
                delta=f"평균 {song_counts.mean():.1f}건/곡"
            )

    # 필터링된 데이터 확인
    if len(filtered_df) == 0:
        st.warning("⚠️ 필터 조건에 맞는 데이터가 없습니다. 필터 범위를 조정해주세요.")
        return

    # 요약 통계
    stats = calculate_summary_stats(filtered_df)

    # 메인 대시보드
    st.markdown("---")

    # 요약 카드 (4개)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📊 총 주문 수",
            value=f"{stats.get('total_orders', 0):,}개",
            delta=f"구매 {stats.get('buy_ratio', 0):.1f}%"
        )

    with col2:
        st.metric(
            label="📈 평균 스프레드율",
            value=f"{stats.get('avg_spread', 0):.2f}%",
            delta=f"{'고평가' if stats.get('avg_spread', 0) > 0 else '저평가'}"
        )

    with col3:
        st.metric(
            label="💰 평균 수익률",
            value=f"{stats.get('avg_yield', 0):.2f}%"
        )

    with col4:
        st.metric(
            label="💧 평균 유동성",
            value=f"{stats.get('avg_liquidity', 0):.1f}점",
            delta=f"대기 {stats.get('waiting_orders', 0)}건"
        )

    st.markdown("---")

    # 차트 섹션 (2개)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 시그널 분포")

        # 시그널 데이터 준비 (pandas 버전 호환)
        signal_counts = filtered_df['signal'].value_counts()
        signal_df = pd.DataFrame({
            '시그널': signal_counts.index,
            '개수': signal_counts.values
        })

        # 비율 계산 추가
        total = signal_df['개수'].sum()
        signal_df['비율'] = (signal_df['개수'] / total * 100).round(1)

        # 디버그 정보 표시
        with st.expander("🔍 데이터 확인 (디버그)"):
            st.write(f"전체 데이터: {len(df)}건")
            st.write(f"필터링 데이터: {len(filtered_df)}건")
            st.write("시그널 분포:")
            st.dataframe(signal_df)

        if len(signal_df) > 0:
            # 도넛 차트 - 명시적으로 비율 텍스트 생성
            signal_df['텍스트'] = signal_df.apply(
                lambda x: f"{x['시그널']}<br>{x['비율']:.1f}%", axis=1
            )

            # 색상 매핑
            color_map = {
                '주의': '#dc2626',
                '유동성↓': '#f59e0b',
                '보통': '#6b7280',
                '저평가, 유동성↓': '#059669',
                '고평가': '#ef4444',
                '저평가': '#10b981',
                '유동성↑': '#3b82f6'
            }
            colors = [color_map.get(sig, '#6b7280') for sig in signal_df['시그널']]

            fig = go.Figure(data=[go.Pie(
                labels=signal_df['시그널'].tolist(),
                values=signal_df['개수'].tolist(),
                hole=0.4,
                text=signal_df['텍스트'].tolist(),
                textinfo='text',
                textposition='inside',
                marker=dict(colors=colors),
                hoverinfo='label+value+percent'
            )])
            fig.update_layout(
                height=350,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.02
                )
            )
            st.plotly_chart(fig, use_container_width=True, key='signal_chart')
        else:
            st.warning("필터링된 데이터가 없습니다.")

    with col2:
        st.subheader("📊 스프레드율 분포")

        if len(filtered_df) > 0:
            # 스프레드율 구간 생성
            bins = [-float('inf'), -20, -10, 10, 20, float('inf')]
            labels = ['매우 저평가\n(< -20%)', '저평가\n(-20~-10%)',
                      '적정\n(-10~10%)', '고평가\n(10~20%)', '매우 고평가\n(> 20%)']

            # 스프레드율 구간 분류
            spread_ranges = pd.cut(
                filtered_df['spread_rate'],
                bins=bins,
                labels=labels
            )

            spread_dist = spread_ranges.value_counts().reindex(labels, fill_value=0)

            # 명시적으로 데이터 변환
            x_values = spread_dist.index.tolist()
            y_values = spread_dist.values.tolist()
            colors = ['#10b981', '#34d399', '#6b7280', '#fb923c', '#ef4444']

            # 바 차트
            fig = go.Figure(data=[
                go.Bar(
                    x=x_values,
                    y=y_values,
                    marker_color=colors,
                    text=y_values,
                    textposition='outside',
                    hovertemplate='%{x}<br>주문 수: %{y}<extra></extra>'
                )
            ])
            fig.update_layout(
                height=350,
                xaxis_title="스프레드율 구간",
                yaxis_title="주문 수",
                showlegend=False,
                yaxis=dict(rangemode='tozero')
            )
            st.plotly_chart(fig, use_container_width=True, key='spread_chart')
        else:
            st.warning("필터링된 데이터가 없습니다.")

    st.markdown("---")

    # 탭으로 테이블 분리
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "💹 작은 스프레드",
        "🔥 고수익률 Top 10",
        "📉 저평가 Top 10",
        "💧 고유동성 Top 10",
        "🎯 가치 투자 기회",
        "📚 카테고리 분석",
        "⏰ 시간 패턴",
        "📋 전체 데이터"
    ])

    with tab1:
        st.subheader("💹 작은 스프레드 주문")
        st.markdown("**매수/매도 가격 차이가 작아 즉시 체결 가능성이 높은 주문**")

        # 스프레드가 작은 주문 필터링 (절대값 5% 이내)
        small_spread = filtered_df[
            (abs(filtered_df['spread_rate']) <= 5.0) &
            (filtered_df['order_status'] == '대기')
        ].copy()

        if len(small_spread) > 0:
            # 스프레드 절대값 기준 정렬
            small_spread['abs_spread'] = abs(small_spread['spread_rate'])
            small_spread_sorted = small_spread.nsmallest(20, 'abs_spread')

            # 요약 정보
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("발견된 주문", f"{len(small_spread):,}개")
            with col2:
                avg_spread = small_spread['spread_rate'].mean()
                st.metric("평균 스프레드", f"{avg_spread:.2f}%")
            with col3:
                buy_count = len(small_spread[small_spread['order_type'] == '구매'])
                st.metric("매수 주문", f"{buy_count}개")
            with col4:
                sell_count = len(small_spread[small_spread['order_type'] == '판매'])
                st.metric("매도 주문", f"{sell_count}개")

            st.markdown("---")

            # 스프레드 분포 차트
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📊 스프레드 분포")
                fig = px.histogram(
                    small_spread,
                    x='spread_rate',
                    nbins=20,
                    labels={'spread_rate': '스프레드율 (%)'},
                    color_discrete_sequence=['#3b82f6']
                )
                fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="최근가")
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True, key='small_spread_hist')

            with col2:
                st.markdown("### 🔄 주문 타입별 분포")
                type_counts = small_spread['order_type'].value_counts()
                fig = px.pie(
                    values=type_counts.values,
                    names=type_counts.index,
                    color_discrete_map={'구매': '#10b981', '판매': '#ef4444'}
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True, key='small_spread_pie')

            # TOP 20 테이블
            st.markdown("### 🏆 TOP 20 작은 스프레드 주문")
            display_cols = small_spread_sorted[
                ['song_name', 'song_artist', 'order_type', 'order_price', 'recent_price',
                 'spread_rate', 'expected_yield', 'liquidity_score', 'signal']
            ]

            display_cols.columns = ['곡명', '아티스트', '타입', '주문가', '최근가',
                                    '스프레드율(%)', '수익률(%)', '유동성', '시그널']

            st.dataframe(
                display_cols.style.format({
                    '주문가': '{:,.0f}원',
                    '최근가': '{:,.0f}원',
                    '스프레드율(%)': '{:.2f}%',
                    '수익률(%)': '{:.2f}%',
                    '유동성': '{:.1f}'
                }).background_gradient(subset=['스프레드율(%)'], cmap='RdYlGn_r'),
                hide_index=True,
                use_container_width=True
            )

            st.info(f"💡 **발견**: {len(small_spread)}개의 작은 스프레드 주문 (±5% 이내, 즉시 체결 가능성 높음)")
        else:
            st.warning("⚠️ 현재 작은 스프레드 조건을 만족하는 주문이 없습니다.")

    with tab2:
        st.subheader("🔥 고수익률 주문 (구매)")
        st.markdown("**투자금 대비 높은 예상 수익률을 제공하는 구매 주문**")

        # 구매 주문만 필터링
        buy_df = filtered_df[filtered_df['order_type'] == '구매']
        top_yield = buy_df.nlargest(10, 'expected_yield')[
            ['song_name', 'song_artist', 'order_price', 'recent_price',
             'expected_yield', 'spread_rate', 'liquidity_score', 'signal']
        ]

        # 컬럼명 변경
        top_yield.columns = ['곡명', '아티스트', '주문가', '최근가',
                             '수익률(%)', '스프레드율(%)', '유동성', '시그널']

        # 스타일 적용
        st.dataframe(
            top_yield.style.format({
                '주문가': '{:,.0f}원',
                '최근가': '{:,.0f}원',
                '수익률(%)': '{:.2f}%',
                '스프레드율(%)': '{:.2f}%',
                '유동성': '{:.1f}'
            }).background_gradient(subset=['수익률(%)'], cmap='Greens'),
            hide_index=True,
            use_container_width=True
        )

    with tab3:
        st.subheader("📉 저평가 주문 (구매)")
        st.markdown("**시장가보다 낮은 가격에 매수할 수 있는 기회**")

        # 구매 주문만 필터링
        buy_df = filtered_df[filtered_df['order_type'] == '구매']
        undervalued = buy_df.nsmallest(10, 'spread_rate')[
            ['song_name', 'song_artist', 'order_price', 'recent_price',
             'spread_rate', 'expected_yield', 'liquidity_score', 'signal']
        ]

        # 컬럼명 변경
        undervalued.columns = ['곡명', '아티스트', '주문가', '최근가',
                               '스프레드율(%)', '수익률(%)', '유동성', '시그널']

        # 스타일 적용
        st.dataframe(
            undervalued.style.format({
                '주문가': '{:,.0f}원',
                '최근가': '{:,.0f}원',
                '스프레드율(%)': '{:.2f}%',
                '수익률(%)': '{:.2f}%',
                '유동성': '{:.1f}'
            }).background_gradient(subset=['스프레드율(%)'], cmap='Greens_r'),
            hide_index=True,
            use_container_width=True
        )

    with tab4:
        st.subheader("💧 고유동성 주문")
        st.markdown("**거래가 활발하여 쉽게 사고팔 수 있는 주문**")

        high_liquidity = filtered_df.nlargest(10, 'liquidity_score')[
            ['song_name', 'song_artist', 'order_price', 'recent_price',
             'liquidity_score', 'spread_rate', 'expected_yield', 'signal']
        ]

        # 컬럼명 변경
        high_liquidity.columns = ['곡명', '아티스트', '주문가', '최근가',
                                  '유동성', '스프레드율(%)', '수익률(%)', '시그널']

        # 스타일 적용
        st.dataframe(
            high_liquidity.style.format({
                '주문가': '{:,.0f}원',
                '최근가': '{:,.0f}원',
                '유동성': '{:.1f}',
                '스프레드율(%)': '{:.2f}%',
                '수익률(%)': '{:.2f}%'
            }).background_gradient(subset=['유동성'], cmap='Blues'),
            hide_index=True,
            use_container_width=True
        )

    with tab5:
        st.subheader("🎯 가치 투자 기회 분석")
        st.markdown("**저평가 + 고수익 + 적정 유동성 조합 발견**")

        # 가치 투자 조건 필터링
        value_opportunities = filtered_df[
            (filtered_df['spread_rate'] < -10) &
            (filtered_df['expected_yield'] > 7) &
            (filtered_df['liquidity_score'] > 30) &
            (filtered_df['order_type'] == '구매')
        ].copy()

        if len(value_opportunities) > 0:
            # 3D 스캐터 플롯
            fig = px.scatter(
                value_opportunities,
                x='spread_rate',
                y='expected_yield',
                size='liquidity_score',
                color='signal',
                hover_data=['song_name', 'song_artist', 'order_price'],
                labels={
                    'spread_rate': '스프레드율 (%)',
                    'expected_yield': '예상 수익률 (%)',
                    'liquidity_score': '유동성 점수'
                },
                title=f'가치 투자 기회 ({len(value_opportunities)}개 발견)',
                color_discrete_map={
                    '저평가': '#10b981',
                    '저평가, 유동성↓': '#059669'
                }
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True, key='value_scatter')

            # 종합 점수 계산 (스프레드율 절대값 + 수익률 + 유동성/10)
            value_opportunities['투자점수'] = (
                abs(value_opportunities['spread_rate']) * 0.3 +
                value_opportunities['expected_yield'] * 0.5 +
                value_opportunities['liquidity_score'] * 0.2
            )

            # TOP 20 테이블
            st.markdown("### 🏆 TOP 20 투자 기회")
            top20 = value_opportunities.nlargest(20, '투자점수')[
                ['song_name', 'song_artist', 'order_price', 'spread_rate',
                 'expected_yield', 'liquidity_score', '투자점수', 'signal']
            ]

            top20.columns = ['곡명', '아티스트', '주문가', '스프레드율(%)',
                            '수익률(%)', '유동성', '투자점수', '시그널']

            st.dataframe(
                top20.style.format({
                    '주문가': '{:,.0f}원',
                    '스프레드율(%)': '{:.2f}%',
                    '수익률(%)': '{:.2f}%',
                    '유동성': '{:.1f}',
                    '투자점수': '{:.1f}'
                }).background_gradient(subset=['투자점수'], cmap='YlGn'),
                hide_index=True,
                use_container_width=True
            )

            st.info(f"💡 **발견**: {len(value_opportunities)}개의 저평가 고수익 기회 (스프레드율 < -10%, 수익률 > 7%, 유동성 > 30점)")
        else:
            st.warning("⚠️ 현재 가치 투자 조건을 만족하는 주문이 없습니다.")

    with tab6:
        st.subheader("📚 저작권 카테고리별 시장 분석")
        st.markdown("**저작재산권과 저작인접권의 가격, 수익률, 유동성 비교 분석**")

        if 'song_category' in filtered_df.columns:
            # 카테고리별 요약 통계
            col1, col2 = st.columns(2)

            categories = filtered_df['song_category'].unique()

            for idx, category in enumerate(categories):
                cat_df = filtered_df[filtered_df['song_category'] == category]

                with col1 if idx == 0 else col2:
                    st.markdown(f"### {category}")
                    st.metric("총 주문 수", f"{len(cat_df):,}개")
                    st.metric("평균 주문가", f"{cat_df['order_price'].mean():,.0f}원")
                    st.metric("평균 수익률", f"{cat_df['expected_yield'].mean():.2f}%")
                    st.metric("평균 유동성", f"{cat_df['liquidity_score'].mean():.1f}점")
                    st.metric("평균 로열티율", f"{cat_df['order_royalty_rate'].mean()*100:.2f}%")

            # 박스 플롯 - 가격 분포
            st.markdown("---")
            st.markdown("### 📊 카테고리별 가격 분포")

            fig = px.box(
                filtered_df,
                x='song_category',
                y='order_price',
                color='song_category',
                labels={'order_price': '주문가 (원)', 'song_category': '카테고리'},
                color_discrete_map={
                    '저작재산권': '#3b82f6',
                    '저작인접권': '#f59e0b'
                }
            )
            fig.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key='category_price_box')

            # 박스 플롯 - 수익률 분포
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 💰 수익률 분포")
                fig = px.box(
                    filtered_df,
                    x='song_category',
                    y='expected_yield',
                    color='song_category',
                    labels={'expected_yield': '수익률 (%)', 'song_category': '카테고리'},
                    color_discrete_map={
                        '저작재산권': '#3b82f6',
                        '저작인접권': '#f59e0b'
                    }
                )
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True, key='category_yield_box')

            with col2:
                st.markdown("### 💧 유동성 분포")
                fig = px.box(
                    filtered_df,
                    x='song_category',
                    y='liquidity_score',
                    color='song_category',
                    labels={'liquidity_score': '유동성 점수', 'song_category': '카테고리'},
                    color_discrete_map={
                        '저작재산권': '#3b82f6',
                        '저작인접권': '#f59e0b'
                    }
                )
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True, key='category_liquidity_box')

        else:
            st.warning("카테고리 데이터가 없습니다.")

    with tab7:
        st.subheader("⏰ 시간대별 주문 패턴 분석")
        st.markdown("**시간대별 주문량, 스프레드율, 수익률 패턴으로 최적 거래시간 파악**")

        # 시간대 데이터 추출 (복사본 생성으로 SettingWithCopyWarning 방지)
        time_df = filtered_df.copy()
        time_df['시간대'] = pd.to_datetime(time_df['order_date']).dt.hour

        # 시간대별 주문 수
        hourly_counts = time_df.groupby('시간대').size().reset_index(name='주문수')

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📊 시간대별 주문 수")
            fig = px.line(
                hourly_counts,
                x='시간대',
                y='주문수',
                markers=True,
                labels={'시간대': '시간 (0-23시)', '주문수': '주문 개수'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True, key='hourly_orders')

        with col2:
            st.markdown("### 📈 시간대별 평균 스프레드율")
            hourly_spread = time_df.groupby('시간대')['spread_rate'].mean().reset_index()
            fig = px.line(
                hourly_spread,
                x='시간대',
                y='spread_rate',
                markers=True,
                labels={'시간대': '시간 (0-23시)', 'spread_rate': '평균 스프레드율 (%)'}
            )
            fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="적정가")
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True, key='hourly_spread')

        # 시간대별 구매/판매 비율
        st.markdown("---")
        st.markdown("### 🔄 시간대별 구매/판매 비율")

        hourly_type = time_df.groupby(['시간대', 'order_type']).size().reset_index(name='개수')
        hourly_type_pivot = hourly_type.pivot(index='시간대', columns='order_type', values='개수').fillna(0)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=hourly_type_pivot.index, y=hourly_type_pivot.get('구매', []),
                             name='구매', marker_color='#10b981'))
        fig.add_trace(go.Bar(x=hourly_type_pivot.index, y=hourly_type_pivot.get('판매', []),
                             name='판매', marker_color='#ef4444'))

        fig.update_layout(
            barmode='group',
            xaxis_title='시간대 (0-23시)',
            yaxis_title='주문 수',
            height=350
        )
        st.plotly_chart(fig, use_container_width=True, key='hourly_type')

        # 시간대별 평균 수익률
        st.markdown("### 💰 시간대별 평균 수익률")
        hourly_yield = time_df.groupby('시간대')['expected_yield'].mean().reset_index()

        fig = px.bar(
            hourly_yield,
            x='시간대',
            y='expected_yield',
            labels={'시간대': '시간 (0-23시)', 'expected_yield': '평균 수익률 (%)'},
            color='expected_yield',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True, key='hourly_yield')

        # 인사이트
        peak_hour = hourly_counts.loc[hourly_counts['주문수'].idxmax(), '시간대']
        best_spread_hour = hourly_spread.loc[hourly_spread['spread_rate'].idxmin(), '시간대']
        best_yield_hour = hourly_yield.loc[hourly_yield['expected_yield'].idxmax(), '시간대']

        st.info(f"""
        💡 **시간대 인사이트**:
        - 📊 가장 활발한 시간: **{peak_hour}시** (주문 {hourly_counts.loc[hourly_counts['시간대']==peak_hour, '주문수'].values[0]}건)
        - 📉 가장 저평가 시간: **{best_spread_hour}시** (평균 스프레드율 {hourly_spread.loc[hourly_spread['시간대']==best_spread_hour, 'spread_rate'].values[0]:.2f}%)
        - 💰 가장 고수익 시간: **{best_yield_hour}시** (평균 수익률 {hourly_yield.loc[hourly_yield['시간대']==best_yield_hour, 'expected_yield'].values[0]:.2f}%)
        """)

    with tab8:
        st.subheader("📋 전체 데이터")
        st.markdown("**모든 주문 데이터를 검색하고 CSV로 다운로드**")

        # 표시할 컬럼 선택
        display_df = filtered_df[
            ['order_date', 'song_name', 'song_artist', 'order_type', 'order_price',
             'recent_price', 'expected_yield', 'spread_rate', 'liquidity_score', 'signal']
        ].copy()

        # 컬럼명 변경
        display_df.columns = ['주문시간', '곡명', '아티스트', '타입', '주문가',
                              '최근가', '수익률(%)', '스프레드율(%)', '유동성', '시그널']

        # 검색 기능
        search = st.text_input("🔍 곡명/아티스트 검색", "")
        if search:
            display_df = display_df[
                display_df['곡명'].str.contains(search, na=False) |
                display_df['아티스트'].str.contains(search, na=False)
            ]

        st.dataframe(
            display_df.style.format({
                '주문가': '{:,.0f}원',
                '최근가': '{:,.0f}원',
                '수익률(%)': '{:.2f}%',
                '스프레드율(%)': '{:.2f}%',
                '유동성': '{:.1f}'
            }),
            hide_index=True,
            use_container_width=True,
            height=400
        )

        # CSV 다운로드
        csv = display_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSV 다운로드",
            data=csv,
            file_name=f"musicow_data_{get_kst_now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    # 추가 통계
    st.markdown("---")
    st.subheader("📈 추가 통계")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**곡별 주문 수 Top 5**")
        song_counts = filtered_df['song_name'].value_counts().head(5)
        for song, count in song_counts.items():
            st.markdown(f"- {song[:30]}... : {count}건")

    with col2:
        st.markdown("**아티스트별 주문 수 Top 5**")
        artist_counts = filtered_df['song_artist'].value_counts().head(5)
        for artist, count in artist_counts.items():
            st.markdown(f"- {artist} : {count}건")

    with col3:
        st.markdown("**주문 상태 분포**")
        status_counts = filtered_df['order_status'].value_counts()
        for status, count in status_counts.items():
            percentage = count / len(filtered_df) * 100
            st.markdown(f"- {status} : {count}건 ({percentage:.1f}%)")


if __name__ == "__main__":
    main()
