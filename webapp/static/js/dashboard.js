// 차트 인스턴스 저장
let signalChart = null;
let premiumChart = null;

// 시그널 색상 매핑
const signalColors = {
    '저평가': '#10b981',
    '고평가': '#ef4444',
    '유동성↑': '#3b82f6',
    '유동성↓': '#f59e0b',
    '주의': '#dc2626',
    '보통': '#6b7280',
    '저평가, 유동성↓': '#059669'
};

// 데이터 로드
async function loadAllData() {
    await Promise.all([
        loadSummary(),
        loadTopYield(),
        loadUndervalued(),
        loadHighLiquidity(),
        loadSignals(),
        loadPremiumDistribution()
    ]);
}

// 요약 통계 로드
async function loadSummary() {
    try {
        const response = await fetch('/api/summary');
        const data = await response.json();

        document.getElementById('total-orders').textContent = data.total_orders.toLocaleString();
        document.getElementById('avg-premium').textContent = `${data.avg_premium}%`;
        document.getElementById('avg-yield').textContent = `${data.avg_yield}%`;
        document.getElementById('avg-liquidity').textContent = data.avg_liquidity.toFixed(1);

        // 색상 적용
        const premiumEl = document.getElementById('avg-premium');
        premiumEl.className = data.avg_premium > 0 ? 'mb-0 positive' : 'mb-0 negative';

        // 마지막 업데이트 시간
        const updateTime = new Date(data.timestamp);
        document.getElementById('last-update').textContent = updateTime.toLocaleString('ko-KR');

    } catch (error) {
        console.error('요약 통계 로드 실패:', error);
    }
}

// 고수익률 테이블 로드
async function loadTopYield() {
    try {
        const response = await fetch('/api/top-yield');
        const data = await response.json();

        const tbody = document.getElementById('top-yield-table');
        tbody.innerHTML = data.map(order => `
            <tr>
                <td>
                    <div class="text-truncate" style="max-width: 150px;" title="${order.song_name}">
                        ${order.song_name}
                    </div>
                    <small class="text-muted">${order.song_artist}</small>
                </td>
                <td class="text-end">
                    <span class="badge bg-success">${order.normalized_yield?.toFixed(2)}%</span>
                </td>
                <td class="text-end ${order.premium < 0 ? 'negative' : 'positive'}">
                    ${order.premium?.toFixed(2)}%
                </td>
            </tr>
        `).join('');

    } catch (error) {
        console.error('고수익률 데이터 로드 실패:', error);
    }
}

// 저평가 테이블 로드
async function loadUndervalued() {
    try {
        const response = await fetch('/api/undervalued');
        const data = await response.json();

        const tbody = document.getElementById('undervalued-table');
        tbody.innerHTML = data.map(order => `
            <tr>
                <td>
                    <div class="text-truncate" style="max-width: 150px;" title="${order.song_name}">
                        ${order.song_name}
                    </div>
                    <small class="text-muted">${order.song_artist}</small>
                </td>
                <td class="text-end negative">
                    <strong>${order.premium?.toFixed(2)}%</strong>
                </td>
                <td class="text-end">
                    ${order.normalized_yield?.toFixed(2)}%
                </td>
            </tr>
        `).join('');

    } catch (error) {
        console.error('저평가 데이터 로드 실패:', error);
    }
}

// 고유동성 테이블 로드
async function loadHighLiquidity() {
    try {
        const response = await fetch('/api/high-liquidity');
        const data = await response.json();

        const tbody = document.getElementById('high-liquidity-table');
        tbody.innerHTML = data.map(order => `
            <tr>
                <td>
                    <div class="text-truncate" style="max-width: 150px;" title="${order.song_name}">
                        ${order.song_name}
                    </div>
                    <small class="text-muted">${order.song_artist}</small>
                </td>
                <td class="text-end">
                    <span class="badge bg-info">${order.liquidity_score?.toFixed(1)}</span>
                </td>
                <td class="text-end ${order.premium < 0 ? 'negative' : 'positive'}">
                    ${order.premium?.toFixed(2)}%
                </td>
            </tr>
        `).join('');

    } catch (error) {
        console.error('고유동성 데이터 로드 실패:', error);
    }
}

// 시그널 차트 로드
async function loadSignals() {
    try {
        const response = await fetch('/api/signals');
        const data = await response.json();

        const ctx = document.getElementById('signalChart').getContext('2d');

        // 기존 차트 제거
        if (signalChart) {
            signalChart.destroy();
        }

        // 새 차트 생성
        signalChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.signal),
                datasets: [{
                    data: data.map(d => d.count),
                    backgroundColor: data.map(d => signalColors[d.signal] || '#6b7280'),
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            padding: 15,
                            font: {
                                size: 12
                            },
                            generateLabels: function(chart) {
                                const data = chart.data;
                                return data.labels.map((label, i) => ({
                                    text: `${label} (${data.datasets[0].data[i].toLocaleString()})`,
                                    fillStyle: data.datasets[0].backgroundColor[i],
                                    hidden: false,
                                    index: i
                                }));
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value.toLocaleString()} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error('시그널 차트 로드 실패:', error);
    }
}

// 괴리율 분포 차트 로드
async function loadPremiumDistribution() {
    try {
        const response = await fetch('/api/premium-distribution');
        const data = await response.json();

        const ctx = document.getElementById('premiumChart').getContext('2d');

        // 기존 차트 제거
        if (premiumChart) {
            premiumChart.destroy();
        }

        // 새 차트 생성
        premiumChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.range),
                datasets: [{
                    label: '주문 수',
                    data: data.map(d => d.count),
                    backgroundColor: [
                        '#10b981',
                        '#34d399',
                        '#6b7280',
                        '#fb923c',
                        '#ef4444'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `주문 수: ${context.parsed.y.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString();
                            }
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error('괴리율 분포 차트 로드 실패:', error);
    }
}

// 페이지 로드 시 데이터 로드
document.addEventListener('DOMContentLoaded', () => {
    loadAllData();

    // 30초마다 자동 새로고침
    setInterval(loadAllData, 30000);
});
