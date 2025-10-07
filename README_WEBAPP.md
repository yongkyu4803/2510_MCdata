# 🌐 뮤직카우 웹 대시보드

Flask + Bootstrap 기반 실시간 시장 분석 대시보드

## 📋 기능

### 실시간 대시보드
- **요약 통계**: 총 주문 수, 평균 프리미엄율, 평균 수익률, 평균 유동성
- **시각화 차트**:
  - 시그널 분포 (도넛 차트)
  - 프리미엄율 분포 (바 차트)
- **Top 10 테이블**:
  - 고수익률 주문
  - 저평가 주문
  - 고유동성 주문

### API 엔드포인트
- `GET /` - 메인 대시보드
- `GET /api/summary` - 요약 통계
- `GET /api/top-yield` - 고수익률 Top 10
- `GET /api/undervalued` - 저평가 Top 10
- `GET /api/high-liquidity` - 고유동성 Top 10
- `GET /api/signals` - 시그널 분포
- `GET /api/premium-distribution` - 프리미엄율 분포

## 🚀 실행 방법

### 1. Flask 웹 서버 시작

```bash
cd webapp
python app.py
```

### 2. 브라우저에서 접속

```
http://localhost:5000
```

## 🏗️ 프로젝트 구조

```
webapp/
├── app.py                 # Flask 애플리케이션
├── templates/
│   └── index.html        # 메인 대시보드 HTML
└── static/
    └── js/
        └── dashboard.js  # 프론트엔드 로직
```

## 🎨 기술 스택

### Backend
- **Flask 3.0+**: Python 웹 프레임워크
- **Flask-CORS**: CORS 지원

### Frontend
- **Bootstrap 5.3**: 반응형 UI 프레임워크
- **Chart.js 4.4**: 차트 라이브러리
- **Font Awesome 6.4**: 아이콘

## 📊 주요 화면

### 요약 카드
- 총 주문 수
- 평균 프리미엄율 (색상 표시)
- 평균 정규화 수익률
- 평균 유동성 점수

### 시각화 차트
1. **시그널 분포 (도넛 차트)**
   - 저평가, 고평가, 유동성↑, 유동성↓, 주의, 보통
   - 각 시그널별 개수 및 비율

2. **프리미엄율 분포 (바 차트)**
   - 매우 저평가 (< -20%)
   - 저평가 (-20% ~ -10%)
   - 적정 (-10% ~ 10%)
   - 고평가 (10% ~ 20%)
   - 매우 고평가 (> 20%)

### 데이터 테이블
1. **고수익률 Top 10**
   - 구매 주문 중 정규화 수익률 높은 순
   - 곡명, 아티스트, 수익률, 프리미엄율 표시

2. **저평가 Top 10**
   - 구매 주문 중 프리미엄율 낮은 순
   - 저평가 주문 우선 표시

3. **고유동성 Top 10**
   - 유동성 점수 높은 순
   - 거래 활발한 곡 우선 표시

## ⚡ 자동 업데이트

- **자동 새로고침**: 30초마다 자동으로 데이터 갱신
- **수동 새로고침**: 우측 하단 새로고침 버튼 클릭

## 🎯 사용 예시

### API 테스트

```bash
# 요약 통계
curl http://localhost:5000/api/summary

# 고수익률 Top 10
curl http://localhost:5000/api/top-yield

# 저평가 Top 10
curl http://localhost:5000/api/undervalued

# 시그널 분포
curl http://localhost:5000/api/signals
```

## 📝 개발 정보

### 개발 시간
- Flask 백엔드: 30분
- Bootstrap UI: 30분
- Chart.js 통합: 20분
- **총 개발 시간**: 1시간 20분

### 성능
- 초기 로딩: ~500ms
- API 응답: ~50ms
- 자동 새로고침: 30초

## 🔧 커스터마이징

### 색상 변경
`templates/index.html` 파일의 CSS 변수 수정:

```css
:root {
    --primary-color: #6366f1;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --danger-color: #ef4444;
    --info-color: #3b82f6;
}
```

### 자동 새로고침 간격 변경
`static/js/dashboard.js` 파일 수정:

```javascript
// 30초 → 원하는 시간(ms)으로 변경
setInterval(loadAllData, 30000);
```

## 🚨 주의사항

- **개발 서버**: 현재는 Flask 개발 서버로 실행
- **프로덕션 배포**: Gunicorn, uWSGI 등 WSGI 서버 사용 권장
- **데이터 소스**: `data/processed/` 디렉토리의 최신 metrics JSON 파일 사용

## 📄 라이센스

MIT License

---

*Last Updated: 2025-10-06*
