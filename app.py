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

# Validate and recalculate total score
def validate_and_fix_scores(analysis_data):
    """Validate scores and recalculate total if necessary"""
    if not analysis_data or 'scores' not in analysis_data:
        return analysis_data
    
    scores = analysis_data['scores']
    calculated_total = 0
    
    # Score keys and their max values
    score_config = {
        '1_trailing_per': 20,
        '2_pbr': 5,
        '3_profit_sustainability': 5,
        '4_duplicate_listing': 5,
        '5_dividend_yield': 10,
        '6_quarterly_dividend': 5,
        '7_dividend_increase_years': 5,
        '8_buyback_cancellation': 7,
        '9_cancellation_ratio': 8,
        '10_treasury_stock': 5,
        '11_growth_potential': 10,
        '12_management': 10,
        '13_global_brand': 5
    }
    
    # Validate and sum up scores
    for key, max_score in score_config.items():
        if key in scores:
            score_value = scores[key].get('score', 0)
            # Ensure score is within valid range
            if score_value < 0:
                score_value = 0
            elif score_value > max_score:
                score_value = max_score
            
            scores[key]['score'] = score_value
            calculated_total += score_value
    
    # If total_score is wildly incorrect (> 100 or negative), fix it
    if 'total_score' not in analysis_data or analysis_data['total_score'] > 100 or analysis_data['total_score'] < 0:
        analysis_data['total_score'] = calculated_total
        st.warning(f"⚠️ 총점이 비정상적이어서 재계산했습니다: {calculated_total}점")
    
    return analysis_data

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
    
    # ULTRA STRICT prompt with EXPLICIT score calculation requirement
    prompt = f"""
You are an elite financial analyst. Analyze '{ticker_or_name}' with MAXIMUM PRECISION.

{korean_instructions}

**ULTRA STRICT RULES:**

1. **ALL DATA MUST BE FOUND** - No "N/A" for basic metrics
2. **MANDATORY SOURCES**: {'Naver Finance (finance.naver.com) FIRST for Korean stocks' if is_korean else 'Yahoo Finance, Investing.com, Google Finance'}
3. **SCORE CALCULATION IS CRITICAL**: You MUST correctly sum all 13 individual scores to get total_score

**Scoring Criteria (MAX 100 POINTS):**

1. Trailing PER (MAX 20): Below 5→20pts | 5-8→15pts | 8-10→10pts | >10→5pts
2. PBR (MAX 5): <0.3→5pts | 0.3-0.6→4pts | 0.6-1.0→3pts | >1.0→0pts
3. Profit Sustainability (MAX 5): Sustainable→5pts | Unstable→0pts
4. Duplicate Listing (MAX 5): No→5pts | Yes→0pts
5. Dividend Yield (MAX 10): >7%→10pts | 5-7%→7pts | 3-5%→5pts | <3%→2pts | None→0pts
6. Quarterly Dividends (MAX 5): Yes→5pts | No→0pts
7. Dividend Increases (MAX 5): 10+yrs→5pts | 5+yrs→4pts | 3+yrs→3pts | None→0pts
8. Regular Buybacks (MAX 7): Yes→7pts | No→0pts
9. Buyback Ratio (MAX 8): >2%→8pts | 1.5-2%→5pts | 0.5-1.5%→3pts | <0.5%→0pts
10. Treasury Stock (MAX 5): None→5pts | <2%→4pts | 2-5%→2pts | >5%→0pts
11. Growth Potential (MAX 10): Very High→10pts | High→7pts | Medium→5pts | Low→3pts
12. Management (MAX 10): Excellent→10pts | Professional→5pts | Poor→0pts
13. Global Brand (MAX 5): Yes→5pts | No→0pts

**CRITICAL: SCORE CALCULATION**
total_score = sum of all 13 individual scores (MUST be between 0-100)

**JSON FORMAT - EXACT STRUCTURE:**

{{
  "company_name": "Official company name",
  "ticker": "Stock symbol",
  "scores": {{
    "1_trailing_per": {{"value": "15.42 (Source)", "score": 5, "reason": "Source: Yahoo Finance"}},
    "2_pbr": {{"value": "10.1 (Source)", "score": 0, "reason": "Source: Investing.com"}},
    "3_profit_sustainability": {{"score": 5, "reason": "Strong recurring revenue"}},
    "4_duplicate_listing": {{"score": 5, "reason": "No subsidiaries listed"}},
    "5_dividend_yield": {{"value": "6.5%", "score": 7, "reason": "Source: Yahoo Finance"}},
    "6_quarterly_dividend": {{"score": 5, "reason": "Quarterly payments"}},
    "7_dividend_increase_years": {{"value": "15 years", "score": 5, "reason": "15 consecutive increases"}},
    "8_buyback_cancellation": {{"score": 7, "reason": "Active program"}},
    "9_cancellation_ratio": {{"value": "1.2%", "score": 3, "reason": "Moderate activity"}},
    "10_treasury_stock": {{"value": "1.5%", "score": 4, "reason": "Low holdings"}},
    "11_growth_potential": {{"score": 7, "reason": "Strong pipeline"}},
    "12_management": {{"score": 10, "reason": "Experienced team"}},
    "13_global_brand": {{"score": 5, "reason": "Globally recognized"}}
  }},
  "total_score": 68,
  "analysis_summary": "Comprehensive 3-4 sentence evaluation."
}}

**EXAMPLE CALCULATION:**
If scores are: 5+0+5+5+7+5+5+7+3+4+7+10+5 = 68 points (NOT 1000000000!)

**FINAL CHECKS:**
- Each individual score MUST be ≤ its maximum
- total_score MUST equal sum of 13 scores
- total_score MUST be between 0-100
- Include specific data sources for all numerical values

Return ONLY the JSON object.
"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Customize domain filter based on stock type
    domain_filter = [
        "finance.naver.com",
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
        "finance.naver.com"
    ]
    
    # Use sonar-pro model
    data = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": f"You are an elite financial analyst. {'For Korean stocks, check Naver Finance FIRST.' if is_korean else ''} You ALWAYS find real data and CORRECTLY calculate total_score by summing all 13 individual scores. Total must be 0-100."},
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
        analysis_data = None
        try:
            analysis_data = json.loads(content)
        except:
            json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', content)
            if json_match:
                analysis_data = json.loads(json_match.group(1))
            else:
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    analysis_data = json.loads(json_match.group())
        
        if not analysis_data:
            st.error("❌ JSON 파싱 실패")
            with st.expander("🔍 AI 응답 내용 보기"):
                st.code(content)
            return None
        
        # CRITICAL: Validate and fix scores
        analysis_data = validate_and_fix_scores(analysis_data)
        
        return analysis_data
            
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
                # Re-validate old data
                analysis_result = validate_and_fix_scores(analysis_result)
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
                total = analysis_result.get('total_score', 0)
                st.metric("총점", f"{total}점", "/100점")
            
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
            # Validate scores before displaying
            analysis = validate_and_fix_scores(analysis)
            
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
st.caption("⚡ Powered by Perplexity AI Sonar-Pro | 데이터는 최대 7일간 캐시 | 실제 재무 데이터 기반 분석")
