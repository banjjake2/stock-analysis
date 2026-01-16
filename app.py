import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import json
import os

# -----------------------------------------------------------------------------
# Stock Mapping Data (한글 종목명 -> 티커 매핑)
# -----------------------------------------------------------------------------
STOCK_MAP = {
    # 한국 주식 (코스피/코스닥)
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "셀트리온": "068270.KS",
    "KB금융": "105560.KS",
    "NAVER": "035420.KS",
    "네이버": "035420.KS",
    "카카오": "035720.KS",
    "POSCO홀딩스": "005490.KS",
    "포스코홀딩스": "005490.KS",
    "삼성물산": "028260.KS",
    "현대모비스": "012330.KS",
    "LG화학": "051910.KS",
    "신한지주": "055550.KS",
    "삼성생명": "032830.KS",
    "에코프로비엠": "247540.KQ",
    "에코프로": "086520.KQ",
    "알테오젠": "196170.KQ",
    
    # 미국 주식 (한글명 지원)
    "애플": "AAPL",
    "마이크로소프트": "MSFT",
    "엔비디아": "NVDA",
    "아마존": "AMZN",
    "구글": "GOOGL",
    "알파벳": "GOOGL",
    "메타": "META",
    "테슬라": "TSLA",
    "브로드컴": "AVGO",
    "넷플릭스": "NFLX",
    "코카콜라": "KO",
    "펩시": "PEP",
    "맥도날드": "MCD",
    "스타벅스": "SBUX",
    "AMD": "AMD",
    "인텔": "INTC",
    "TSMC": "TSM",
    "마이크론": "MU"
}

# 티커 -> 한글명 역매핑 (즐겨찾기 표시용)
REVERSE_STOCK_MAP = {v: k for k, v in STOCK_MAP.items()}

def get_ticker_code(input_text):
    """한글 종목명을 입력받으면 티커로 변환, 아니면 대문자로 반환"""
    if not input_text:
        return ""
    clean_text = input_text.strip()
    # 매핑 테이블에 있으면 해당 티커 반환
    if clean_text in STOCK_MAP:
        return STOCK_MAP[clean_text]
    # 없으면 대문자로 변환해서 반환 (직접 티커 입력한 경우)
    return clean_text.upper()

def get_display_name(ticker):
    """티커에 해당하는 한글명이 있으면 '종목명(티커)' 형태로 반환"""
    name = REVERSE_STOCK_MAP.get(ticker)
    if name:
        return f"{name} ({ticker})"
    return ticker

# -----------------------------------------------------------------------------
# Persistence Functions (파일 저장/로드)
# -----------------------------------------------------------------------------
FAVORITES_FILE = "favorites.json"

def load_favorites():
    """파일에서 즐겨찾기 목록을 불러옵니다."""
    if os.path.exists(FAVORITES_FILE):
        try:
            with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_favorites(fav_list):
    """즐겨찾기 목록을 파일에 저장합니다."""
    try:
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            json.dump(fav_list, f, ensure_ascii=False)
    except Exception as e:
        st.error(f"즐겨찾기 저장 중 오류 발생: {e}")

# -----------------------------------------------------------------------------
# Session State Initialization (즐겨찾기 및 현재 티커 관리)
# -----------------------------------------------------------------------------
if 'favorites' not in st.session_state:
    st.session_state['favorites'] = load_favorites() # 파일에서 로드

if 'current_ticker' not in st.session_state:
    st.session_state['current_ticker'] = "NVDA"

def update_ticker(ticker):
    st.session_state['current_ticker'] = ticker

def add_favorite(ticker):
    if ticker not in st.session_state['favorites']:
        st.session_state['favorites'].append(ticker)
        save_favorites(st.session_state['favorites']) # 변경 시 저장

def remove_favorite(ticker):
    if ticker in st.session_state['favorites']:
        st.session_state['favorites'].remove(ticker)
        save_favorites(st.session_state['favorites']) # 변경 시 저장

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def get_currency_symbol(ticker):
    """티커에 따라 통화 기호를 반환"""
    if ticker.endswith(".KS") or ticker.endswith(".KQ"):
        return "₩"
    return "$"

def format_large_currency(value, symbol="$"):
    """큰 금액을 B(10억), M(100만) 단위로 변환"""
    if pd.isna(value) or value == 0: return "-"
    abs_value = abs(value)
    
    # 한국 원화(₩)인 경우 단위 조정 (조, 억)
    if symbol == "₩":
        if abs_value >= 1_000_000_000_000: # 1조
            return f"{symbol} {value / 1_000_000_000_000:,.1f}조"
        elif abs_value >= 100_000_000: # 1억
            return f"{symbol} {value / 100_000_000:,.0f}억"
        else:
            return f"{symbol} {value:,.0f}"
    
    # 달러($) 등 기타 통화
    else:
        if abs_value >= 1_000_000_000: return f"{symbol} {value / 1_000_000_000:,.2f} B"
        elif abs_value >= 1_000_000: return f"{symbol} {value / 1_000_000:,.2f} M"
        else: return f"{symbol} {value:,.0f}"

# -----------------------------------------------------------------------------
# Page Config & Layout
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Stock Analysis Pro", page_icon="📈", layout="wide")

st.title("📈 주식 재무 분석 (한글 검색 지원)")
st.markdown("Yahoo Finance 데이터를 기반으로 **매출, 영업이익, EPS, PER 범위, 부채비율**을 분석합니다.")

# --- 1. 추천 종목 버튼 ---
st.subheader("📌 추천 종목")
presets = [
    ("현대차", "005380.KS"), 
    ("MSFT", "MSFT"), 
    ("AAPL", "AAPL"), 
    ("GOOGL", "GOOGL"), 
    ("META", "META"), 
    ("TSLA", "TSLA")
]

# 버튼을 가로로 배치
cols = st.columns(len(presets))
for idx, (name, ticker_code) in enumerate(presets):
    if cols[idx].button(name, use_container_width=True):
        update_ticker(ticker_code)

# --- 2. 즐겨찾기 목록 ---
if st.session_state['favorites']:
    st.subheader("⭐ 나의 즐겨찾기")
    # 한 줄에 여러 개 배치 (반응형 고려 4~6개)
    fav_cols = st.columns(6) 
    for i, fav_ticker in enumerate(st.session_state['favorites']):
        col_idx = i % 6
        # 버튼 라벨에 한글명도 같이 표시 (예: 삼성전자 (005930.KS))
        btn_label = get_display_name(fav_ticker)
        
        # 버튼 그룹 (이동 및 삭제)
        with fav_cols[col_idx]:
            if st.button(f"{btn_label}", key=f"go_{fav_ticker}", use_container_width=True):
                update_ticker(fav_ticker)
            if st.button(f"❌ 삭제", key=f"del_{fav_ticker}", help=f"{btn_label} 삭제"):
                remove_favorite(fav_ticker)
                st.rerun()
        
    st.divider()

# -----------------------------------------------------------------------------
# Main Logic
# -----------------------------------------------------------------------------
# 검색창
input_val = st.text_input("종목명 또는 티커 입력 (예: 삼성전자, NVDA)", key='current_ticker')

# 입력값을 실제 티커로 변환
target_ticker = get_ticker_code(input_val)

if target_ticker:
    # 한글 입력 시 변환된 티커를 사용자에게 알려줌
    if input_val != target_ticker:
        st.caption(f"🔍 '{input_val}' -> '{target_ticker}'로 검색합니다.")

    # 즐겨찾기 추가 버튼
    col1, col2 = st.columns([1, 5])
    with col1:
        if target_ticker not in st.session_state['favorites']:
            if st.button(f"⭐ 즐겨찾기 추가"):
                add_favorite(target_ticker)
                st.rerun()
        else:
            st.info("✅ 즐겨찾기 등록됨")

    try:
        with st.spinner(f'{get_display_name(target_ticker)} 데이터 분석 중...'):
            stock = yf.Ticker(target_ticker)
            
            # 1. 데이터 가져오기 (재무제표 & 대차대조표 & 주가)
            fin = stock.financials
            bs = stock.balance_sheet
            hist = stock.history(period="5y") 
            
            if fin.empty or bs.empty:
                st.error(f"'{input_val}' ({target_ticker})의 데이터를 찾을 수 없습니다. 정확한 티커를 입력해주세요.")
                st.stop()

            # ---------------------------------------------------------
            # 2. 데이터 전처리
            # ---------------------------------------------------------
            # 통화 기호 결정
            currency_symbol = get_currency_symbol(target_ticker)

            # 재무제표 (Income Statement)
            df_fin = fin.T
            df_fin.index = pd.to_datetime(df_fin.index)

            # 대차대조표 (Balance Sheet)
            df_bs = bs.T
            df_bs.index = pd.to_datetime(df_bs.index)

            # 데이터 병합
            df_merged = df_fin.join(df_bs, lsuffix='_fin', rsuffix='_bs', how='inner')

            # ---------------------------------------------------------
            # 3. 2021년 이후 데이터 필터링
            # ---------------------------------------------------------
            df_merged = df_merged[df_merged.index.year >= 2021]
            df_merged = df_merged.sort_index(ascending=True)

            if df_merged.empty:
                st.warning("2021년 이후의 재무 데이터가 없습니다.")
                st.stop()

            # ---------------------------------------------------------
            # 4. 주요 컬럼 추출 및 계산
            # ---------------------------------------------------------
            rev_col = next((c for c in df_merged.columns if 'Total Revenue' in c), None)
            op_col = next((c for c in df_merged.columns if 'Operating Income' in c), None)
            
            # 부채비율 (Total Liabilities 기준)
            liab_col = next((c for c in df_merged.columns if 'Total Liabilities Net Minority Interest' in c), None)
            if not liab_col:
                liab_col = next((c for c in df_merged.columns if 'Total Liabilities' in c), None)
            
            equity_col = next((c for c in df_merged.columns if 'Stockholders Equity' in c), None)
            if not equity_col:
                 equity_col = next((c for c in df_merged.columns if 'Common Stock Equity' in c), None)

            # EPS
            eps_col = next((c for c in df_merged.columns if 'Diluted EPS' in c), None)
            if not eps_col:
                eps_col = next((c for c in df_merged.columns if 'Basic EPS' in c), None)

            result_data = []

            for date_idx, row in df_merged.iterrows():
                year = date_idx.year
                
                revenue = row[rev_col] if rev_col else 0
                op_income = row[op_col] if op_col else 0
                
                # 부채비율
                debt_ratio_str = "-"
                if liab_col and equity_col:
                    liabilities = row[liab_col]
                    equity = row[equity_col]
                    if pd.notnull(liabilities) and pd.notnull(equity) and equity != 0:
                        debt_ratio = liabilities / equity
                        debt_ratio_str = f"{debt_ratio:.2f}"
                
                # EPS & PER
                hist_year = hist[hist.index.year == year]
                per_range_str = "-"
                eps = row[eps_col] if eps_col else None
                eps_str = f"{eps:,.0f}" if currency_symbol == "₩" else f"{eps:.2f}" # 원화 EPS는 소수점 제거

                if not hist_year.empty and eps and eps > 0:
                    year_low = hist_year['Low'].min()
                    year_high = hist_year['High'].max()
                    low_per = year_low / eps
                    high_per = year_high / eps
                    per_range_str = f"{low_per:.1f} ~ {high_per:.1f}배"
                elif eps and eps <= 0:
                    per_range_str = "N/A (적자)"

                result_data.append({
                    "년도": str(year),
                    "매출 (Revenue)": format_large_currency(revenue, currency_symbol),
                    "영업이익 (Operating Income)": format_large_currency(op_income, currency_symbol),
                    "EPS": eps_str,
                    "PER 범위 (Year High/Low)": per_range_str,
                    "부채비율 (Debt Ratio)": debt_ratio_str
                })

            # ---------------------------------------------------------
            # 5. 결과 출력
            # ---------------------------------------------------------
            df_result = pd.DataFrame(result_data)
            
            st.subheader(f"📊 {get_display_name(target_ticker)} 연도별 분석")
            
            st.dataframe(
                df_result,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "년도": st.column_config.TextColumn("년도", width="small"),
                    "매출 (Revenue)": st.column_config.TextColumn(f"매출 ({currency_symbol})"),
                    "영업이익 (Operating Income)": st.column_config.TextColumn(f"영업이익 ({currency_symbol})"),
                    "EPS": st.column_config.TextColumn("EPS", help="주당 순이익"),
                    "PER 범위 (Year High/Low)": st.column_config.TextColumn("PER 범위 (최저~최고)", help="해당 연도 주가 범위 / EPS"),
                    "부채비율 (Debt Ratio)": st.column_config.TextColumn("부채비율 (Ratio)", help="총부채 / 자본총계"),
                }
            )

            st.caption("※ 데이터 출처: Yahoo Finance. 한국 주식의 경우 '.KS'(코스피) 또는 '.KQ'(코스닥) 접미사가 필요합니다.")

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")