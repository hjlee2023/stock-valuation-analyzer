# 📊 저평가 우량주 자동 분석기

Perplexity AI API를 활용한 종목 자동 평가 및 랭킹 시스템

## 🌟 주요 기능

- **자동 종목 분석**: 종목명 또는 티커만 입력하면 13가지 평가 기준으로 자동 분석
- **스마트 캐싱**: 7일 이내 분석 결과는 재사용하여 API 비용 절감
- **실시간 랭킹**: 모든 분석 결과를 총점 기준으로 자동 랭킹
- **자동 업데이트**: 7일 이상 된 분석은 자동으로 갱신

## 📋 평가 기준 (총 100점)

1. **Trailing PER** (20점)
2. **직전 분기 PBR** (5점)
3. **이익 지속 가능성** (5점)
4. **중복 상장 여부** (5점)
5. **배당수익률** (10점)
6. **분기 배당 실시** (5점)
7. **배당 연속 인상 연수** (5점)
8. **자사주 매입 및 소각** (7점)
9. **연간 소각 비율** (8점)
10. **자사주 보유 비율** (5점)
11. **미래 성장 잠재력** (10점)
12. **기업 경영** (10점)
13. **세계적 브랜드** (5점)

## 🚀 실행 방법

### 1. 로컬 실행

```bash
# 저장소 클론
git clone https://github.com/hjlee2023/stock-valuation-analyzer.git
cd stock-valuation-analyzer

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 앱 실행
streamlit run app.py
```

### 2. Streamlit Cloud 배포

1. GitHub 저장소를 Streamlit Cloud에 연결
2. `app.py`를 메인 파일로 선택
3. 배포 완료!

## 🔑 API 키 설정

1. [Perplexity AI](https://www.perplexity.ai/)에서 API 키 발급
2. 앱 사이드바에서 API 키 입력

### Streamlit Cloud에서 API 키 설정 (선택사항)

`.streamlit/secrets.toml` 파일 생성:

```toml
PERPLEXITY_API_KEY = "your-api-key-here"
```

## 💾 데이터 저장

- 분석 결과는 `analysis_data/analyses.json`에 저장됩니다
- 각 종목별 마지막 분석 시간이 기록됩니다
- 7일 이내 재분석 요청 시 기존 결과를 재사용합니다

## 📱 사용 방법

1. **종목 분석 탭**
   - 종목명 또는 티커 입력 (예: 삼성전자, 005930)
   - "분석 시작" 버튼 클릭
   - 세부 점수 및 종합 평가 확인

2. **전체 랭킹 탭**
   - 분석된 모든 종목의 랭킹 확인
   - Top 3 종목 하이라이트
   - 분석일 기준 정렬

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **AI API**: Perplexity AI (Llama 3.1 Sonar Large)
- **Data Storage**: JSON (로컬 파일)
- **Hosting**: Streamlit Cloud / GitHub

## 📝 라이센스

MIT License

## 👨‍💻 개발자

약학과 3학년 재학생 - 금융 및 코딩에 관심이 많습니다!
