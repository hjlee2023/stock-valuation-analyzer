import streamlit as st
import os
from datetime import datetime, timedelta
import json
from pathlib import Path
import requests
import re

# Page config
st.set_page_config(
    page_title="저평가 우량주 분석기",
    page_icon="📊",
    layout="wide"
)

# Initialize data directory
DATA_DIR = Path("analysis_data")
DATA_DIR.mkdir(exist_ok=True)
ANALYSIS_FILE = DATA_DIR / "analyses.json"

# Get API key from Streamlit secrets or environment variable
def get_api_key():
    try:
        api_key = st.secrets["PERPLEXITY_API_KEY"]
        return api_key
    except Exception as e:
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            st.error("⚠️ 서비스 오류: 관리자에게 문의하세요.")
            st.stop()
        return api_key

# Load existing analyses
def load_analyses():
    if ANALYSIS_FILE.exists():
        with open(ANALYSIS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Save analyses
def save_analyses(analyses):
    with open(ANALYSIS_FILE, 'w', encoding='utf-8') as f:
        json.dump(analyses, f, ensure_ascii=False, indent=2)

# Detect if Korean stock based on input
def is_korean_stock(ticker_or_name):
    """Detect if the input is likely a Korean stock"""
    # Check for Korean characters
    if re.search(r'[\uac00-\ud7a3]', ticker_or_name):
        return True
    # Check for 6-digit Korean stock code
    if re.match(r'^\d{6}$', ticker_or_name.strip()):
        return True
    # Known Korean stock tickers
    korean_tickers = ['005930', '086790', '000660', '035420', '051910', '105560', '055550', '035720', '096770']
    if ticker_or_name.strip() in korean_tickers:
        return True
    return False

# Perplexity API call with ULTRA STRICT prompt
def analyze_stock_with_perplexity(ticker_or_name, api_key):
    url = "https://api.perplexity.ai/chat/completions"
    
    # Detect if Korean stock for customized prompt
    is_korean = is_korean_stock(ticker_or_name)
    
    # Korean-specific instructions
    korean_instructions = """
**한국 주식 특별 지침:**
- PRIMARY SOURCE: 네이버 금융 (finance.naver.com) - 필수 우선 검색
- KRX (한국거래소) 데이터 활용
- 기업 IR 페이지 확인
- 한국 금융주 (하나금융지주, 기업은행, KB금융 등)는 2023년부터 분기 배당 실시 중
- 한국어로 "하나금융지주 분기배당" 검색 필수
- 예시: 하나금융지주는 2023년부터 분기별 배당 (906원 x 4회)
""" if is_korean else ""
    
    # ULTRA STRICT prompt
    prompt = f"""
You are an elite financial analyst. Analyze '{ticker_or_name}' with MAXIMUM PRECISION.

{korean_instructions}

**ULTRA STRICT RULES - VIOLATION IS UNACCEPTABLE:**

1. **ALL DATA MUST BE FOUND:**
   - For ANY publicly traded company, P/E and P/B ratios ALWAYS exist
   - For dividend-paying companies, dividend frequency (quarterly/annual) ALWAYS exists
   - Saying "not available", "not specified", or "N/A" for basic metrics is FORBIDDEN

2. **MANDATORY DATA SOURCES:**
   {'- **KOREAN STOCKS**: Naver Finance (finance.naver.com) - USE THIS FIRST!' if is_korean else ''}
   - Yahoo Finance (finance.yahoo.com) - PRIMARY for non-Korean stocks
   - Google Finance - Secondary source
   - Investing.com - Alternative source
   - Company official IR page - For corporate actions

3. **SPECIFIC SEARCH INSTRUCTIONS:**
   - P/E Ratio: {'Search on Naver Finance first' if is_korean else 'Search on Yahoo Finance'}
   - P/B Ratio: {'Check Naver Finance 주요재무정보' if is_korean else 'Yahoo Finance or Investing.com'}
   - Dividend Frequency: {'Search "분기배당" or check company IR' if is_korean else 'Check company IR or dividend sites'}
   - {'**CRITICAL**: Korean financial stocks (banks, insurance) often pay QUARTERLY dividends since 2023!' if is_korean else ''}

4. **REAL EXAMPLES:**
   {'- 하나금융지주: Quarterly dividend (906원 x 4), 4.81% yield' if is_korean else ''}
   {'- 삼성전자: Semi-annual dividend, check Naver Finance' if is_korean else ''}
   - Pfizer: Quarterly dividend ($0.43 x 4), 6.51% yield, P/B ~1.8-1.9

5. **ZERO TOLERANCE POLICY:**
   - "Data not available" = FAILURE
   - "Not specified" for dividend frequency = UNACCEPTABLE
   - Empty P/E, P/B values = REJECTION

**Required Data Points:**

1. **Trailing P/E Ratio**: {'Naver Finance or' if is_korean else ''} Yahoo Finance, Investing.com
2. **Price-to-Book Ratio (P/B)**: {'Naver Finance 주요재무정보 or' if is_korean else ''} Financial sites
3. **Dividend Yield**: Percentage from major sites
4. **Dividend Frequency**: Quarterly/Semi-annual/Annual - MUST specify
5. **Dividend History**: 10-year track record
6. **Share Buybacks**: Recent announcements
7. **Treasury Stock**: Company balance sheet

**Scoring Criteria:**

1. Trailing PER: Below 5: 20pts | 5-8: 15pts | 8-10: 10pts | Above 10: 5pts
2. PBR: Below 0.3: 5pts | 0.3-0.6: 4pts | 0.6-1.0: 3pts | Above 1.0: 0pts
3. Profit Sustainability: Sustainable: 5pts | Unstable: 0pts
4. Duplicate Listing: No: 5pts | Yes: 0pts
5. Dividend Yield: Above 7%: 10pts | 5-7%: 7pts | 3-5%: 5pts | Below 3%: 2pts | None: 0pts
6. Quarterly Dividends: Yes: 5pts | No: 0pts
7. Dividend Increases: 10+yrs: 5pts | 5+yrs: 4pts | 3+yrs: 3pts | None: 0pts
8. Regular Buybacks: Yes: 7pts | No: 0pts
9. Buyback Ratio: Above 2%: 8pts | 1.5-2%: 5pts | 0.5-1.5%: 3pts | Below: 0pts
10. Treasury Stock: None: 5pts | Below 2%: 4pts | 2-5%: 2pts | Above 5%: 0pts
11. Growth Potential: Very High: 10pts | High: 7pts | Medium: 5pts | Low: 3pts
12. Management: Excellent: 10pts | Professional: 5pts | Poor: 0pts
13. Global Brand: Yes: 5pts | No: 0pts

**JSON FORMAT ONLY:**

{{
  "company_name": "Official name",
  "ticker": "Symbol",
  "scores": {{
    "1_trailing_per": {{"value": "15.42 (Yahoo Finance)", "score": 5, "reason": "Source: [specific site]"}},
    "2_pbr": {{"value": "1.88 (Investing.com)", "score": 0, "reason": "Source: [site]"}},
    "3_profit_sustainability": {{"score": 5, "reason": "Business stability"}},
    "4_duplicate_listing": {{"score": 5, "reason": "No subsidiaries listed"}},
    "5_dividend_yield": {{"value": "6.51% (Yahoo Finance)", "score": 7, "reason": "Source: [site]"}},
    "6_quarterly_dividend": {{"score": 5, "reason": "Pays quarterly - Source: [site]"}},
    "7_dividend_increase_years": {{"value": "15 years", "score": 5, "reason": "History from [source]"}},
    "8_buyback_cancellation": {{"score": 7, "reason": "Active program"}},
    "9_cancellation_ratio": {{"value": "1.2%", "score": 3, "reason": "Data from [source]"}},
    "10_treasury_stock": {{"value": "1.5%", "score": 4, "reason": "Balance sheet"}},
    "11_growth_potential": {{"score": 7, "reason": "Growth analysis"}},
    "12_management": {{"score": 10, "reason": "Leadership quality"}},
    "13_global_brand": {{"score": 5, "reason": "Brand recognition"}}
  }},
  "total_score": 78,
  "analysis_summary": "3-4 sentence comprehensive evaluation with key investment thesis."
}}

**FINAL WARNING:**
For major stocks, saying "not available" for P/E, P/B, or dividend frequency = FAILURE.
{'For Korean stocks, CHECK NAVER FINANCE FIRST - it has the most accurate Korean stock data!' if is_korean else ''}

Return ONLY the JSON object.
"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Customize domain filter based on stock type
    domain_filter = [
        "finance.naver.com",  # Korean stocks priority
        "finance.yahoo.com",
        "investing.com",
        "marketwatch.com",
        "seekingalpha.com",
        "gurufocus.com"
    ] if is_korean else [
        "finance.yahoo.com",
        "investing.com",
        "marketwatch.com",
        "seekingalpha.com",
        "gurufocus.com",
        "finance.naver.com"  # Still included but lower priority
    ]
    
    # Use sonar-pro model with maximum settings
    data = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": f"You are an elite financial analyst. {'For Korean stocks, you ALWAYS check Naver Finance (finance.naver.com) FIRST. Korean financial companies often pay quarterly dividends since 2023.' if is_korean else ''} You NEVER fail to find P/E, P/B, and dividend data for publicly traded companies. You cite specific sources."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 8000,
        "search_domain_filter": domain_filter,
        "return_citations": True,
        "search_recency_filter": "month"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=180)
        
        if response.status_code != 200:
            error_detail = f"Status: {response.status_code}"
            try:
                error_json = response.json()
                error_detail += f"\n{json.dumps(error_json, indent=2)}"
            except:
                error_detail += f"\n{response.text}"
            
            st.error(f"❌ API 요청 실패")
            with st.expander("🔍 상세 오류 내용 보기"):
                st.code(error_detail)
            return None
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Try to parse JSON from the content
        try:
            analysis_data = json.loads(content)
            return analysis_data
        except:
            json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', content)
            if json_match:
                analysis_data = json.loads(json_match.group(1))
                return analysis_data
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                analysis_data = json.loads(json_match.group())
                return analysis_data
            
            st.error("❌ JSON 파싱 실패")
            with st.expander("🔍 AI 응답 내용 보기"):
                st.code(content)
            return None
            
    except requests.exceptions.Timeout:
        st.error("⏱️ 요청 시간 초과 (180초). 다시 시도해주세요.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"🌐 네트워크 오류: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ 예상치 못한 오류: {str(e)}")
        import traceback
        with st.expander("🔍 상세 오류 로그"):
            st.code(traceback.format_exc())
        return None

# Main app
st.title("📊 저평가 우량주 자동 분석기")
st.markdown("---")

# Get API key
API_KEY = get_api_key()

# Main content
tab1, tab2 = st.tabs(["📈 종목 분석", "🏆 전체 랭킹"])

with tab1:
    st.header("종목 분석")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker_input = st.text_input("종목명 또는 티커를 입력하세요", placeholder="예: 삼성전자, 005930, AAPL, Pfizer, 하나금융지주")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_btn = st.button("🔍 분석 시작", type="primary", use_container_width=True)
    
    if analyze_btn and ticker_input:
        # Load existing analyses
        analyses = load_analyses()
        
        # Check if analysis exists and is recent
        ticker_key = ticker_input.strip().upper()
        existing = analyses.get(ticker_key)
        
        analysis_result = None
        
        if existing:
            last_analysis_date = datetime.fromisoformat(existing['timestamp'])
            days_old = (datetime.now() - last_analysis_date).days
            
            if days_old < 7:
                st.info(f"📋 기존 분석 결과 사용 (분석일: {last_analysis_date.strftime('%Y-%m-%d %H:%M')})")
                analysis_result = existing['data']
            else:
                st.warning(f"🔄 마지막 분석이 {days_old}일 전입니다. 새로운 분석을 진행합니다.")
                with st.spinner('🤖 최고 성능 AI로 실제 재무 데이터를 검색하고 분석하고 있습니다... (약 60-120초 소요)'):
                    analysis_result = analyze_stock_with_perplexity(ticker_input, API_KEY)
                    
                    if analysis_result:
                        analyses[ticker_key] = {
                            'timestamp': datetime.now().isoformat(),
                            'data': analysis_result
                        }
                        save_analyses(analyses)
                        st.success("✅ 분석 완료 및 저장됨")
        else:
            with st.spinner('🤖 최고 성능 AI로 실제 재무 데이터를 검색하고 분석하고 있습니다... (약 60-120초 소요)'):
                analysis_result = analyze_stock_with_perplexity(ticker_input, API_KEY)
                
                if analysis_result:
                    analyses[ticker_key] = {
                        'timestamp': datetime.now().isoformat(),
                        'data': analysis_result
                    }
                    save_analyses(analyses)
                    st.success("✅ 분석 완료 및 저장됨")
        
        # Display results
        if analysis_result:
            st.success(f"✅ 분석 완료: {analysis_result.get('company_name', ticker_input)}")
            
            # Total score display
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col2:
                st.metric("총점", f"{analysis_result['total_score']}점", "/100점")
            
            # Summary
            st.markdown("### 📝 종합 평가")
            st.info(analysis_result.get('analysis_summary', '종합 평가 없음'))
            
            # Detailed scores
            st.markdown("### 📊 세부 점수")
            
            scores = analysis_result.get('scores', {})
            
            criteria = [
                ("1. Trailing PER", "1_trailing_per", 20),
                ("2. 직전 분기 PBR", "2_pbr", 5),
                ("3. 이익 지속 가능성", "3_profit_sustainability", 5),
                ("4. 중복 상장 여부", "4_duplicate_listing", 5),
                ("5. 배당수익률", "5_dividend_yield", 10),
                ("6. 분기 배당 실시", "6_quarterly_dividend", 5),
                ("7. 배당 연속 인상 연수", "7_dividend_increase_years", 5),
                ("8. 자사주 매입 및 소각", "8_buyback_cancellation", 7),
                ("9. 연간 소각 비율", "9_cancellation_ratio", 8),
                ("10. 자사주 보유 비율", "10_treasury_stock", 5),
                ("11. 미래 성장 잠재력", "11_growth_potential", 10),
                ("12. 기업 경영", "12_management", 10),
                ("13. 세계적 브랜드", "13_global_brand", 5)
            ]
            
            for title, key, max_score in criteria:
                if key in scores:
                    item = scores[key]
                    score = item.get('score', 0)
                    reason = item.get('reason', '')
                    value = item.get('value', '')
                    
                    with st.expander(f"{title}: {score}/{max_score}점"):
                        if value:
                            st.write(f"**값:** {value}")
                        st.write(f"**평가:** {reason}")

with tab2:
    st.header("🏆 전체 종목 랭킹")
    
    analyses = load_analyses()
    
    if not analyses:
        st.info("아직 분석된 종목이 없습니다. 먼저 종목을 분석해주세요!")
    else:
        # Create ranking list
        ranking_data = []
        for ticker, data in analyses.items():
            analysis = data['data']
            ranking_data.append({
                '순위': 0,
                '종목명': analysis.get('company_name', ticker),
                '티커': analysis.get('ticker', ticker),
                '총점': analysis.get('total_score', 0),
                '분석일': datetime.fromisoformat(data['timestamp']).strftime('%Y-%m-%d')
            })
        
        # Sort by total score
        ranking_data.sort(key=lambda x: x['총점'], reverse=True)
        
        # Add ranking
        for i, item in enumerate(ranking_data):
            item['순위'] = i + 1
        
        # Display ranking table
        st.dataframe(
            ranking_data,
            use_container_width=True,
            hide_index=True
        )
        
        # Top 3 highlight
        if len(ranking_data) >= 3:
            st.markdown("---")
            st.subheader("🥇 Top 3 종목")
            cols = st.columns(3)
            
            for i, col in enumerate(cols[:3]):
                with col:
                    item = ranking_data[i]
                    st.metric(
                        f"#{i+1} {item['종목명']}",
                        f"{item['총점']}점",
                        f"분석일: {item['분석일']}"
                    )

# Footer
st.markdown("---")
st.caption("⚡ Powered by Perplexity AI Sonar-Pro | 한국 주식은 네이버금융 우선 검색 | 데이터는 최대 7일간 캐시 | 실제 재무 데이터 기반 분석")
