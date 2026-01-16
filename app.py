import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# -----------------------------------------------------------------------------
# Helper Functions (포맷팅 함수)
# -----------------------------------------------------------------------------
def format_large_currency(value):
    """큰 금액을 B(10억), M(100만) 단위로 변환"""
    if pd.isna(value) or value == 0: return "-"
    abs_value = abs(value)
    if abs_value >= 1_000_000_000: return f"$ {value / 1_000_000_000:,.2f} B"
    elif abs_value >= 1_000_000: return f"$ {value / 1_000_000:,.2f} M"
    else: return f"$ {value:,.0f}"

# -----------------------------------------------------------------------------
# Page Config
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Stock Financial Analysis", page_icon="📈", layout="wide")

st.title("📈 미국 주식 재무 분석 (2021 ~ 현재)")
st.markdown("Yahoo Finance 데이터를 기반으로 **매출, 영업이익, EPS, PER 범위, 부채비율**을 분석합니다.")

# -----------------------------------------------------------------------------
# Main Logic
# -----------------------------------------------------------------------------
ticker = st.text_input("티커 입력 (예: NVDA, AAPL, TSLA)", value="NVDA").upper()

if ticker:
    try:
        with st.spinner(f'{ticker} 데이터 분석 중...'):
            stock = yf.Ticker(ticker)
            
            # 1. 데이터 가져오기 (재무제표 & 대차대조표 & 주가)
            fin = stock.financials
            bs = stock.balance_sheet
            # PER 계산을 위해 넉넉하게 5년치 주가 데이터를 가져옴
            hist = stock.history(period="5y") 
            
            if fin.empty or bs.empty:
                st.error("재무 데이터를 가져올 수 없습니다. 티커를 확인해 주세요.")
                st.stop()

            # ---------------------------------------------------------
            # 2. 데이터 전처리 (행/열 변환 및 날짜 처리)
            # ---------------------------------------------------------
            # 재무제표 (Income Statement)
            df_fin = fin.T  # 행열 전환 (날짜가 인덱스로 옴)
            df_fin.index = pd.to_datetime(df_fin.index) # 인덱스를 날짜형으로 변환

            # 대차대조표 (Balance Sheet)
            df_bs = bs.T
            df_bs.index = pd.to_datetime(df_bs.index)

            # 데이터 병합 (날짜 기준)
            # merge시 인덱스가 유지되도록 설정
            df_merged = df_fin.join(df_bs, lsuffix='_fin', rsuffix='_bs', how='inner')

            # ---------------------------------------------------------
            # 3. 2021년 이후 데이터만 필터링
            # ---------------------------------------------------------
            df_merged = df_merged[df_merged.index.year >= 2021]
            
            # 날짜 오름차순 정렬 (과거 -> 현재)
            df_merged = df_merged.sort_index(ascending=True)

            if df_merged.empty:
                st.warning("2021년 이후의 재무 데이터가 아직 업데이트되지 않았거나 없습니다.")
                st.stop()

            # ---------------------------------------------------------
            # 4. 주요 컬럼 추출 및 계산
            # ---------------------------------------------------------
            
            # (1) 매출 및 영업이익 컬럼 찾기
            rev_col = next((c for c in df_merged.columns if 'Total Revenue' in c), None)
            op_col = next((c for c in df_merged.columns if 'Operating Income' in c), None)
            
            # (2) 부채비율 계산 수정: Total Liabilities (총부채) 기준 적용
            # 사용자 데이터 (1.35, 1.19, 1.00, 0.76)는 총부채/자본 비율과 일치함.
            
            # Total Liabilities Net Minority Interest 가 보통 총부채를 의미함
            liab_col = next((c for c in df_merged.columns if 'Total Liabilities Net Minority Interest' in c), None)
            if not liab_col: # 못 찾으면 그냥 Total Liabilities 시도
                liab_col = next((c for c in df_merged.columns if 'Total Liabilities' in c), None)
            
            equity_col = next((c for c in df_merged.columns if 'Stockholders Equity' in c), None)
            if not equity_col: # 못 찾으면 Common Stock Equity 시도
                 equity_col = next((c for c in df_merged.columns if 'Common Stock Equity' in c), None)

            # EPS (Diluted EPS 우선, 없으면 Basic)
            eps_col = next((c for c in df_merged.columns if 'Diluted EPS' in c), None)
            if not eps_col:
                eps_col = next((c for c in df_merged.columns if 'Basic EPS' in c), None)

            # 결과 리스트 담기
            result_data = []

            for date_idx, row in df_merged.iterrows():
                year = date_idx.year
                
                # --- A. 매출/영업이익 ---
                revenue = row[rev_col] if rev_col else 0
                op_income = row[op_col] if op_col else 0
                
                # --- B. 부채비율 ---
                debt_ratio_str = "-"
                if liab_col and equity_col:
                    liabilities = row[liab_col]
                    equity = row[equity_col]
                    if pd.notnull(liabilities) and pd.notnull(equity) and equity != 0:
                        debt_ratio = liabilities / equity # 100을 곱하지 않음 (비율 형태)
                        debt_ratio_str = f"{debt_ratio:.2f}"
                
                # --- C. EPS 및 PER 범위 계산 ---
                hist_year = hist[hist.index.year == year]
                per_range_str = "-"
                
                eps = row[eps_col] if eps_col else None
                eps_str = f"{eps:.2f}" if eps is not None else "-"
                
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
                    "매출 (Revenue)": format_large_currency(revenue),
                    "영업이익 (Operating Income)": format_large_currency(op_income),
                    "EPS": eps_str,
                    "PER 범위 (Year High/Low)": per_range_str,
                    "부채비율 (Debt Ratio)": debt_ratio_str
                })

            # ---------------------------------------------------------
            # 5. 결과 출력
            # ---------------------------------------------------------
            df_result = pd.DataFrame(result_data)
            
            st.subheader(f"📊 {ticker} 연도별 분석 (2021 ~ Current)")
            
            st.dataframe(
                df_result,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "년도": st.column_config.TextColumn("년도", width="small"),
                    "매출 (Revenue)": st.column_config.TextColumn("매출 (Revenue)"),
                    "영업이익 (Operating Income)": st.column_config.TextColumn("영업이익 (Operating Income)"),
                    "EPS": st.column_config.TextColumn("EPS", help="주당 순이익 (Diluted EPS)"),
                    "PER 범위 (Year High/Low)": st.column_config.TextColumn("PER 범위 (최저~최고)", help="해당 연도 최저가/최고가를 EPS로 나눈 값"),
                    "부채비율 (Debt Ratio)": st.column_config.TextColumn("부채비율 (Ratio)", help="총부채(Total Liabilities) / 자본총계 (1.0 = 100%)"),
                }
            )

            st.caption("※ 데이터 출처: Yahoo Finance. 부채비율은 '총부채/자본총계' 기준입니다.")

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
        st.write("상세 에러 내용:", e) # 디버깅용