# 📊 저평가 우량주 자동 분석기

Perplexity AI API를 활용한 종목 자동 평가 및 랭킹 시스템

## 🎯 주요 기능

- **자동 종목 분석**: 종목명 또는 티커만 입력하면 13가지 평가 기준으로 자동 분석
- **스마트 캐싱**: 7일 이내 분석된 종목은 기존 결과 재사용 (API 비용 절감)
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

## 🚀 빠른 시작

### Streamlit Cloud 배포 (추천)

1. 이 저장소를 Fork 또는 Clone
2. [Streamlit Cloud](https://streamlit.io/cloud)에 로그인
3. "New app" 클릭
4. Repository: `hjlee2023/stock-valuation-analyzer`
5. Main file: `app.py`
6. **Secrets 설정** (중요!):
   - Settings → Secrets 메뉴 선택
   - 다음 내용 입력:
     ```toml
     PERPLEXITY_API_KEY = "pplx-your-api-key-here"
     ```
7. Deploy 클릭!

### 로컬 실행

```bash
# 저장소 클론
git clone https://github.com/hjlee2023/stock-valuation-analyzer.git
cd stock-valuation-analyzer

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 환경 변수 설정
export PERPLEXITY_API_KEY="pplx-your-api-key-here"
# Windows: set PERPLEXITY_API_KEY=pplx-your-api-key-here

# 앱 실행
streamlit run app.py
```

## 🔑 API 키 설정

### 1. Perplexity API 키 발급

1. [Perplexity AI](https://www.perplexity.ai/) 로그인
2. Settings → API 메뉴
3. API 키 생성 및 복사

### 2. API 키 등록

**Streamlit Cloud 배포 시:**
- Dashboard → App Settings → Secrets
- `.streamlit/secrets.toml.example` 파일 참고하여 입력

**로컬 실행 시:**
```bash
# Linux/Mac
export PERPLEXITY_API_KEY="your-api-key-here"

# Windows
set PERPLEXITY_API_KEY=your-api-key-here
```

## 💰 API 비용 절감 전략

- **7일 캐싱**: 같은 종목은 7일 이내 재분석하지 않음
- **효율적 프롬프트**: 한 번의 API 호출로 모든 평가 완료
- **예상 비용**: 종목당 약 4,000 토큰 (약 $0.01)

## 📱 사용 방법

### 종목 분석
1. "종목 분석" 탭 선택
2. 종목명 또는 티커 입력 (예: 삼성전자, 005930)
3. "분석 시작" 버튼 클릭
4. 세부 점수 및 종합 평가 확인

### 랭킹 확인
1. "전체 랭킹" 탭 선택
2. 분석된 모든 종목의 순위 확인
3. Top 3 종목 하이라이트 확인

## 📊 데이터 저장

- 분석 결과는 `analysis_data/analyses.json`에 저장
- 각 종목별 마지막 분석 시간 기록
- 7일 이내 재분석 시 기존 결과 재사용

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **AI API**: Perplexity AI (Llama 3.1 Sonar Large)
- **Data Storage**: JSON (로컬 파일)
- **Hosting**: Streamlit Cloud / GitHub

## 📝 주의사항

⚠️ **API 키 보안**
- API 키를 절대 코드에 하드코딩하지 마세요
- Streamlit Secrets 또는 환경 변수 사용 필수
- `.gitignore`에 `.streamlit/secrets.toml` 포함됨

⚠️ **데이터 정확성**
- AI 분석 결과는 참고용입니다
- 투자 결정 전 반드시 추가 검증 필요
- 실시간 데이터가 아닐 수 있음

## 🔧 문제 해결

### API 키 오류
```
⚠️ API 키가 설정되지 않았습니다
```
→ Streamlit Cloud Secrets 또는 환경 변수 확인

### JSON 파싱 실패
```
JSON 파싱 실패
```
→ API 응답 형식 문제, 다시 시도하거나 이슈 제보

## 🤝 기여

이슈와 PR은 언제나 환영합니다!

## 📄 라이선스

MIT License

## 👨‍💻 개발자

약학과 3학년 재학생 - 금융 및 코딩에 관심이 많습니다!

---

⚡ **Powered by Perplexity AI**
