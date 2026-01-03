import streamlit as st
import os
from datetime import datetime, timedelta
import json
from pathlib import Path
import requests

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

# Perplexity API call with ULTRA STRICT prompt
def analyze_stock_with_perplexity(ticker_or_name, api_key):
    url = "https://api.perplexity.ai/chat/completions"
    
    # ULTRA STRICT prompt - NO EXCUSES for missing data
    prompt = f"""
You are an elite financial analyst. Analyze '{ticker_or_name}' with MAXIMUM PRECISION.

**ULTRA STRICT RULES - VIOLATION IS UNACCEPTABLE:**

1. **ALL DATA MUST BE FOUND:**
   - For ANY publicly traded company, P/E and P/B ratios ALWAYS exist
   - For dividend-paying companies, dividend frequency (quarterly/annual) ALWAYS exists
   - Saying "not available", "not specified", or "N/A" for basic metrics is FORBIDDEN

2. **MANDATORY DATA SOURCES:**
   - Yahoo Finance (finance.yahoo.com) - PRIMARY source for P/E, P/B, dividends
   - Google Finance - Secondary source
   - Investing.com - Alternative source
   - Company official IR page - For corporate actions
   - For Korean stocks: Naver Finance (finance.naver.com)
   - For Brazilian stocks: Investing.com, Yahoo Finance

3. **SPECIFIC SEARCH INSTRUCTIONS:**
   - P/E Ratio: Search "[company] trailing PE ratio" on Yahoo Finance
   - P/B Ratio: Search "[company] price to book ratio" on Yahoo Finance or Investing.com
   - Dividend Yield: Search "[company] dividend yield" - readily available everywhere
   - Dividend Frequency: Search "[company] dividend payment schedule" or check company IR
   - Example: For Pfizer, P/B ratio is ~1.8-1.9 (easily found on multiple sites)

4. **QUALITY VERIFICATION:**
   - Each numerical value MUST cite the exact source website
   - If first search fails, try at least 3 different sources
   - Cross-reference data between multiple sources for accuracy
   - For well-known companies (S&P 500, KOSPI 200, etc.), ALL data is publicly available

5. **ZERO TOLERANCE POLICY:**
   - "Data not available" response = FAILURE
   - "Not specified in results" = UNACCEPTABLE
   - Empty values for P/E, P/B of listed companies = REJECTION

**Required Data Points with NO EXCEPTIONS:**

1. **Trailing P/E Ratio**: Find from Yahoo Finance, Google Finance, or Investing.com
2. **Price-to-Book Ratio (P/B)**: Find from Yahoo Finance, Investing.com, or GuruFocus
3. **Dividend Yield (if applicable)**: Percentage from any major financial site
4. **Dividend Frequency**: Quarterly/Semi-annual/Annual - check company IR or dividend sites
5. **Dividend History**: 10-year track record from dividend history sites
6. **Share Buybacks**: Recent announcements from company news or SEC filings
7. **Treasury Stock**: From company balance sheet

**Scoring Criteria (UNCHANGED):**

1. Trailing PER:
   - Below 5: 20 points | 5-8: 15 points | 8-10: 10 points | Above 10: 5 points

2. Latest Quarter PBR:
   - Below 0.3: 5 points | 0.3-0.6: 4 points | 0.6-1.0: 3 points | Above 1.0: 0 points

3. Profit Sustainability: Sustainable: 5 points | Unstable: 0 points

4. Duplicate Listing: No: 5 points | Yes: 0 points

5. Dividend Yield:
   - Above 7%: 10 points | 5-7%: 7 points | 3-5%: 5 points | Below 3%: 2 points | None: 0 points

6. Quarterly Dividends: Yes: 5 points | No: 0 points

7. Consecutive Dividend Increases:
   - 10+ years: 5 points | 5+ years: 4 points | 3+ years: 3 points | None: 0 points

8. Regular Buybacks: Yes (annual+): 7 points | No: 0 points

9. Annual Buyback Ratio:
   - Above 2%: 8 points | 1.5-2%: 5 points | 0.5-1.5%: 3 points | Below 0.5%: 0 points

10. Treasury Stock Ratio:
    - None: 5 points | Below 2%: 4 points | 2-5%: 2 points | Above 5%: 0 points

11. Growth Potential: Very High: 10 | High: 7 | Medium: 5 | Low: 3

12. Management Quality: Excellent: 10 | Professional: 5 | Poor: 0

13. Global Brand: Yes: 5 points | No: 0 points

**STRICT JSON FORMAT - NO TEXT OUTSIDE JSON:**

{{
  "company_name": "Full official name",
  "ticker": "Stock symbol",
  "scores": {{
    "1_trailing_per": {{"value": "15.42 (Yahoo Finance)", "score": 5, "reason": "Source: Yahoo Finance - trailing P/E as of [date]"}},
    "2_pbr": {{"value": "1.88 (Investing.com)", "score": 0, "reason": "Source: Investing.com P/B ratio"}},
    "3_profit_sustainability": {{"score": 5, "reason": "Strong recurring revenue model"}},
    "4_duplicate_listing": {{"score": 5, "reason": "No subsidiaries publicly listed"}},
    "5_dividend_yield": {{"value": "6.51% (Yahoo Finance)", "score": 7, "reason": "Source: Yahoo Finance dividend yield"}},
    "6_quarterly_dividend": {{"score": 5, "reason": "Pays quarterly dividends - confirmed on company IR"}},
    "7_dividend_increase_years": {{"value": "15 years", "score": 5, "reason": "15 consecutive years of dividend increases"}},
    "8_buyback_cancellation": {{"score": 7, "reason": "Active buyback program as of [recent date]"}},
    "9_cancellation_ratio": {{"value": "1.2%", "score": 3, "reason": "Moderate buyback activity"}},
    "10_treasury_stock": {{"value": "1.5%", "score": 4, "reason": "Source: Company balance sheet"}},
    "11_growth_potential": {{"score": 7, "reason": "Strong pipeline and market position"}},
    "12_management": {{"score": 10, "reason": "Experienced leadership team"}},
    "13_global_brand": {{"score": 5, "reason": "Globally recognized pharmaceutical brand"}}
  }},
  "total_score": 78,
  "analysis_summary": "Comprehensive 3-4 sentence evaluation with key findings and investment thesis."
}}

**FINAL WARNING:**
If you return "not available" or "N/A" for P/E, P/B, or dividend frequency of a major listed company, you have FAILED this task. These are basic metrics available on every financial website. SEARCH HARDER and FIND THE DATA.

Return ONLY the JSON object. No explanatory text before or after.
"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Use sonar-pro model (most powerful) with maximum settings
    data = {
        "model": "sonar-pro",  # UPGRADED TO MOST POWERFUL MODEL
        "messages": [
            {"role": "system", "content": "You are an elite financial analyst who NEVER fails to find data. For any publicly traded company, you ALWAYS find P/E ratio, P/B ratio, and dividend information from web sources like Yahoo Finance, Google Finance, or Investing.com. Saying 'data not available' for basic metrics is grounds for immediate failure."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,  # ZERO temperature for maximum accuracy
        "max_tokens": 8000,  # Maximum tokens for thorough analysis
        "search_domain_filter": ["finance.yahoo.com", "finance.naver.com", "investing.com", "marketwatch.com", "seekingalpha.com", "gurufocus.com"],
        "return_citations": True,
        "search_recency_filter": "month"  # Recent data only
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=180)  # 3 minute timeout for thorough search
        
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
        import re
        
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
        ticker_input = st.text_input("종목명 또는 티커를 입력하세요", placeholder="예: 삼성전자, 005930, AAPL, Pfizer, 페트로브라스")
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
                        # Update with new analysis
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
                    # Save new analysis
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
st.caption("⚡ Powered by Perplexity AI Sonar-Pro | 데이터는 최대 7일간 캐시됩니다. | 실제 재무 데이터 기반 분석")
