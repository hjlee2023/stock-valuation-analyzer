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
        # Try Streamlit secrets first (for cloud deployment)
        api_key = st.secrets["PERPLEXITY_API_KEY"]
        return api_key
    except Exception as e:
        # Fallback to environment variable (for local development)
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            st.error("⚠️ API 키가 설정되지 않았습니다.")
            st.info("""
            **관리자에게 문의하세요:**
            
            Streamlit Cloud에서 다음과 같이 설정해야 합니다:
            1. Settings → Secrets
            2. 다음 내용 추가:
            ```
            PERPLEXITY_API_KEY = "pplx-your-api-key"
            ```
            """)
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

# Perplexity API call
def analyze_stock_with_perplexity(ticker_or_name, api_key):
    url = "https://api.perplexity.ai/chat/completions"
    
    prompt = f"""
다음 평가 기준에 따라 '{ticker_or_name}' 종목을 분석하고 점수를 매겨주세요.

평가 항목:
1. Trailing PER
   - 5 미만: 20점
   - 5 이상 8 미만: 15점
   - 8 이상 10 미만: 10점
   - 10 이상: 5점

2. 직전 분기 PBR
   - 0.3 미만: 5점
   - 0.3 이상 0.6 미만: 4점
   - 0.6 이상 1.0 미만: 3점
   - 1.0 이상: 0점

3. 이익 지속 가능성 (정성적 판단)
   - 대체로 지속 가능: 5점
   - 불안정한 이익 창출력: 0점

4. 중복 상장 여부 (자회사/손자회사 상장 여부)
   - 중복상장: 0점
   - 단독상장: 5점

5. 배당수익률
   - 7% 초과: 10점
   - 5% 초과 7% 이하: 7점
   - 3% 초과 5% 이하: 5점
   - 3% 이하: 2점

6. 분기 배당 실시 여부
   - 예: 5점
   - 아니요: 0점

7. 배당 연속 인상 연수
   - 10년 이상: 5점
   - 5년 이상: 4점
   - 3년 이상: 3점
   - 해당 없음: 0점

8. 정기적 자사주 매입 및 소각 여부 (연 1회 이상)
   - 예: 7점
   - 아니요: 0점

9. 연간 자사주 소각 비율 (총주식수 대비)
   - 2% 초과: 8점
   - 1.5% 초과 2% 이하: 5점
   - 0.5% 초과 1.5% 이하: 3점
   - 0.5% 이하: 0점

10. 자사주 보유 비율
    - 없음: 5점
    - 2% 미만: 4점
    - 2% 이상 5% 미만: 2점
    - 5% 이상: 0점

11. 미래 성장 잠재력 (정성적 판단)
    - 매우 높다: 10점
    - 높다: 7점
    - 보통: 5점
    - 낮다: 3점

12. 기업 경영 (경영자 평가)
    - 우수한 경영자: 10점
    - 전문 경영자: 5점
    - 저조한 실적의 오너 경영: 0점

13. 세계적 브랜드 보유 여부
    - 있다: 5점
    - 없다: 0점

반드시 다음 JSON 형식으로만 답변하세요. 다른 설명 없이 JSON만 반환하세요:
{{
  "company_name": "회사명",
  "ticker": "티커",
  "scores": {{
    "1_trailing_per": {{"value": "10.5", "score": 10, "reason": "간단한 설명"}},
    "2_pbr": {{"value": "0.8", "score": 3, "reason": "간단한 설명"}},
    "3_profit_sustainability": {{"score": 5, "reason": "판단 근거"}},
    "4_duplicate_listing": {{"score": 5, "reason": "판단 근거"}},
    "5_dividend_yield": {{"value": "3.5%", "score": 5, "reason": "간단한 설명"}},
    "6_quarterly_dividend": {{"score": 0, "reason": "판단 근거"}},
    "7_dividend_increase_years": {{"value": "5년", "score": 4, "reason": "간단한 설명"}},
    "8_buyback_cancellation": {{"score": 7, "reason": "판단 근거"}},
    "9_cancellation_ratio": {{"value": "1.2%", "score": 3, "reason": "간단한 설명"}},
    "10_treasury_stock": {{"value": "1.5%", "score": 4, "reason": "간단한 설명"}},
    "11_growth_potential": {{"score": 7, "reason": "판단 근거"}},
    "12_management": {{"score": 10, "reason": "판단 근거"}},
    "13_global_brand": {{"score": 5, "reason": "판단 근거"}}
  }},
  "total_score": 68,
  "analysis_summary": "전체 종합 평가 (3-4문장)"
}}
"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.1-sonar-large-128k-online",
        "messages": [
            {"role": "system", "content": "당신은 금융 분석 전문가입니다. 최신 재무 데이터를 기반으로 정확한 분석을 JSON 형식으로만 제공합니다."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        
        # Detailed error handling
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
                
                if response.status_code == 401:
                    st.warning("🔑 API 키가 유효하지 않습니다. Streamlit Secrets 설정을 확인하세요.")
                elif response.status_code == 400:
                    st.warning("⚠️ 요청 형식에 문제가 있습니다.")
            return None
        
        result = response.json()
        
        # Extract JSON from response
        content = result['choices'][0]['message']['content']
        
        # Try to parse JSON from the content
        import re
        
        # First try: direct JSON parse
        try:
            analysis_data = json.loads(content)
            return analysis_data
        except:
            # Second try: extract JSON from markdown code block
            json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', content)
            if json_match:
                analysis_data = json.loads(json_match.group(1))
                return analysis_data
            
            # Third try: find any JSON object
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                analysis_data = json.loads(json_match.group())
                return analysis_data
            
            # If all fails, show the raw response
            st.error("❌ JSON 파싱 실패")
            with st.expander("🔍 AI 응답 내용 보기"):
                st.code(content)
            return None
            
    except requests.exceptions.Timeout:
        st.error("⏱️ 요청 시간 초과 (60초). 다시 시도해주세요.")
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

if API_KEY:
    # Show API key status (masked)
    with st.sidebar:
        st.success(f"✅ API 키 설정 완료")
        st.caption(f"Key: {API_KEY[:8]}...{API_KEY[-4:]}")

# Main content
tab1, tab2 = st.tabs(["📈 종목 분석", "🏆 전체 랭킹"])

with tab1:
    st.header("종목 분석")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker_input = st.text_input("종목명 또는 티커를 입력하세요", placeholder="예: 삼성전자, 005930, AAPL")
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
                with st.spinner('🤖 AI가 종목을 분석하고 있습니다... (약 30-60초 소요)'):
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
            with st.spinner('🤖 AI가 종목을 분석하고 있습니다... (약 30-60초 소요)'):
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
st.caption("⚡ Powered by Perplexity AI | 데이터는 최대 7일간 캐시됩니다.")
