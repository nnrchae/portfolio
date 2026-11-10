import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
from datetime import datetime, timedelta
import plotly.graph_objects as go
import re

# ---------------------------------------------------------
# 0. 페이지 설정 및 월가 기관 투자자 터미널 테마 CSS
# ---------------------------------------------------------
st.set_page_config(page_title="WALL STREET INSTITUTIONAL ASSET TERMINAL", layout="wide")

st.markdown("""
<style>
    /* 월가 터미널 다크 네이비/차콜 배경 및 프로페셔널 폰트 */
    .main {
        background-color: #0e1117;
        color: #c9d1d9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    h1 {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #f0f6fc !important;
        letter-spacing: -0.5px;
        border-bottom: 2px solid #30363d;
        padding-bottom: 15px;
    }
    h2, h3, .section-title {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        color: #58a6ff !important;
        border-left: 4px solid #1f6feb;
        padding-left: 10px;
        margin-top: 35px;
        margin-bottom: 15px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    p, li, span, label, div {
        color: #8b949e !important;
        font-size: 1.05rem !important;
    }
    /* 월가 스타일 메트릭 카드 */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #f0f6fc !important;
        font-family: 'Courier New', Courier, monospace;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        color: #8b949e !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    [data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px 20px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    /* 인스티튜셔널 다크 테이블 디자인 */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 20px;
    }
    .custom-table th {
        background-color: #21262d !important;
        color: #f0f6fc !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        padding: 12px 16px !important;
        text-align: left;
        border-bottom: 2px solid #30363d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .custom-table td {
        font-size: 1.0rem !important;
        padding: 12px 16px !important;
        color: #c9d1d9 !important;
        border-bottom: 1px solid #21262d !important;
        font-family: 'Courier New', Courier, monospace;
    }
    .custom-table tr:hover {
        background-color: #1f242c !important;
    }
    /* 사이드바 프로페셔널 튜닝 */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏛️ INSTITUTIONAL ASSET MANAGEMENT TERMINAL")
st.markdown(f"**MARKET DATE:** {datetime.now().strftime('%Y-%m-%d')} &nbsp;|&nbsp; **MANDATE:** 7-Year Net Worth 2X Growth & Multi-Account Risk Engine")
st.markdown("<hr style='border: 1px solid #30363d; margin-top: 10px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. [동적 데이터 입력 레이어] 최신 잔고 데이터 기본 고정 (탭 구분 완벽 지원)
# ---------------------------------------------------------
st.markdown("### 📥 PORTFOLIO DATA INGESTION")

default_raw_data = """구분	계좌번호	종목명	손익률	평가손익	잔고수량	매입단가	매입금액	평가금액	대출금액	평가비중
예수금	340-375-915-01		0	0	0	0	0	154,079,041	0	27.86%
예수금	363-810-976-01		0	0	0	0	0	345,478	0	0.06%
예수금	376-640-119-01		0	0	0	0	0	1,881,569	0	0.34%
주식	340-375-915-01	SK하이닉스	-37.95	-6,948,810	10	1,830,881.00	18,308,810	11,360,000	0	2.05%
주식	340-375-915-01	삼성전자	-22.01	-16,082,530	300	243,508.00	73,052,530	56,970,000	0	10.30%
주식	363-810-976-01	TIGER 미국배당다우존스타겟데일리커버드콜	-2.46	-922,960	3,683	10,161.00	37,421,490	36,498,530	0	6.60%
주식	376-640-119-01	TIGER 미국배당다우존스타겟데일리커버드콜	-5.48	-408,535	711	10,485.00	7,454,545	7,046,010	0	1.27%
주식	376-640-119-01	SOL AI반도체TOP2플러스	-54.3	-69,810,364	5,000	25,712.00	128,560,364	58,750,000	0	10.62%
퇴직연금	870-126-269-01	TIGER 미국배당다우존스타겟데일리커버드콜	-2.46	-250	1	0	10,160	9,910	0	0%
퇴직연금	870-126-269-01	PLUS 코스피50	-38.63	-985,670	27	0	2,551,400	1,565,730	0	0.28%
퇴직연금	870-126-269-01	TIGER 미국배당다우존스타겟데일리커버드콜	0.83	408,085	5,011	0	49,250,925	49,659,010	0	8.98%
퇴직연금	870-126-269-01	TIGER 200	-9.48	-655,540	80	0	6,917,140	6,261,600	0	1.13%
퇴직연금	870-126-269-01	ACE KRX금현물	-21.53	-682,660	100	0	3,170,160	2,487,500	0	0.44%
퇴직연금	870-126-269-01	SOL AI반도체TOP2플러스	-47.34	-57,382,550	5,433	0	121,220,300	63,837,750	0	11.54%
퇴직연금	870-126-269-01	PLUS 코스피50	-39.39	-18,841,695	500	0	47,836,695	28,995,000	0	5.24%
퇴직연금	870-126-269-01	ACE 미국30년국채액티브	1.75	14,960	100	0	854,540	869,500	0	0.15%
퇴직연금	870-126-269-01	현금자산	0	0	72,328,871	0	72,328,871	72,328,871	0	13.08%"""

user_raw_input = st.text_area("ASSET FEEDBACK BUFFER (TAB-SEPARATED):", value=default_raw_data, height=120)

def parse_user_asset_text(raw_text):
    lines = raw_text.strip().split("\n")
    parsed_rows = []
    for line in lines:
        if not line.strip(): continue
        tokens = [t.strip() for t in line.split('\t') if t.strip()]
        if len(tokens) < 2:
            tokens = line.strip().split()
        if len(tokens) < 2: continue
        if tokens[0] not in ["예수금", "주식", "퇴직연금"]:
            if "구분" in tokens[0] or "종목명" in line: continue
            
        gubun = tokens[0]
        account = "기타계좌"
        acc_idx = -1
        for i, t in enumerate(tokens):
            if re.match(r'\d{3}-\d+-\d+', t):
                account = t
                acc_idx = i
                break
        if acc_idx == -1: continue
        
        remainder = tokens[acc_idx+1:]
        if not remainder: continue
        
        all_floats = []
        for t in remainder:
            t_clean = t.replace(',', '').replace('%', '')
            try:
                all_floats.append(float(t_clean))
            except ValueError:
                pass
                
        eval_amount = 0.0
        buy_amount = 0.0
        if all_floats:
            amounts = [f for f in all_floats if f > 1000]
            if amounts:
                eval_amount = amounts[-1]
                buy_amount = amounts[-2] if len(amounts) >= 2 else eval_amount
            else:
                eval_amount = all_floats[-1]
                buy_amount = all_floats[-2] if len(all_floats) >= 2 else eval_amount

        account_label = "위탁계좌" if "340" in account or "363" in account or "376" in account else "퇴직연금(870)"
        
        stock_name_tokens = [t for t in remainder if not re.match(r'^-?\d+(\.\d+)?%?$', t.replace(',', ''))]
        stock_name = " ".join(stock_name_tokens) if stock_name_tokens else "현금성자산"
        if "예수금" in gubun or not stock_name_tokens: stock_name = "예수금/현금"

        if "예수금" in gubun or "현금" in stock_name: asset_group = "현금"
        elif "반도체" in stock_name or "삼성" in stock_name or "하이닉스" in stock_name: asset_group = "반도체"
        elif "미국배당" in stock_name: asset_group = "미국배당"
        elif "코스피" in stock_name or "200" in stock_name: asset_group = "국내지수"
        else: asset_group = "대체/채권"
            
        is_irp_risk = True if "퇴직연금" in account_label and asset_group not in ["현금", "대체/채권"] else False

        parsed_rows.append({
            "계좌": account_label,
            "구분": asset_group,
            "종목명": stock_name,
            "매입금액": buy_amount if buy_amount > 0 else eval_amount,
            "평가금액": eval_amount if eval_amount > 0 else buy_amount,
            "연금위험자산": is_irp_risk
        })
    return pd.DataFrame(parsed_rows)

df_port = parse_user_asset_text(user_raw_input)
if df_port.empty or df_port["평가금액"].sum() == 0:
    st.warning("⚠️ ASSET INGESTION PARSE ERROR.")
    st.stop()

total_asset = df_port["평가금액"].sum()

# ---------------------------------------------------------
# 2. [기술적 분석 데이터 연동]
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def load_technical_data():
    start_date = (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d')
    target_tickers = {"현대차": "005380", "삼성전자": "005930", "SK하이닉스": "000660", "SOL AI반도체TOP2": "466920", "TIGER 미국배당다우존스": "489250"}
    tech_results = {}
    for name, code in target_tickers.items():
        try:
            pdf = fdr.DataReader(code, start_date)
            cur_price = pdf['Close'].iloc[-1]
            ma20 = pdf['Close'].rolling(20).mean().iloc[-1]
            ma20_status = "🟢 MA20 BELOW (ACCUMULATE)" if cur_price < ma20 else "🔴 MA20 ABOVE (PREMIUM)"
            std20 = pdf['Close'].rolling(20).std().iloc[-1]
            bb_lower = ma20 - (2 * std20)
            bb_status = "🟢 BB LOWER (OVERSOLD)" if cur_price <= bb_lower * 1.02 else "⚪ NORMAL BAND"
            delta = pdf['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            cur_rsi = (100 - (100 / (1 + rs))).iloc[-1]
            rsi_status = f"🟢 RSI {cur_rsi:.1f} (OVERSOLD)" if cur_rsi <= 35 else (f"🔴 RSI {cur_rsi:.1f} (OVERBOUGHT)" if cur_rsi >= 65 else f"⚪ RSI {cur_rsi:.1f} (NEUTRAL)")
            pdf['TradeValue'] = pdf['Close'] * pdf['Volume']
            vol_5 = pdf['TradeValue'].rolling(5).mean().iloc[-1]
            vol_20 = pdf['TradeValue'].rolling(20).mean().iloc[-1]
            vol_status = "🟢 VOLUME INFLOW" if vol_5 > vol_20 * 1.2 else "⚪ VOLUME FLAT"
            score = 0
            if cur_price < ma20: score += 1
            if cur_price <= bb_lower * 1.02: score += 1
            if cur_rsi <= 35: score += 1
            if vol_5 > vol_20 * 1.2: score += 1
            action = "🟢 [STRONG ACCUMULATION]" if score >= 3 else ("🟡 [SCALE-IN / WATCH]" if score == 2 else "⚪ [HOLD / NEUTRAL]")

            tech_results[name] = {
                "CURRENT PRICE": f"{int(cur_price):,} KRW",
                "MA20 SIGNAL": ma20_status,
                "BOLLINGER BAND": bb_status,
                "RSI METER": rsi_status,
                "VOLUME DYNAMICS": vol_status,
                "QUANTITATIVE ACTION": action
            }
        except Exception:
            tech_results[name] = {"CURRENT PRICE": "N/A", "MA20 SIGNAL": "-", "BOLLINGER BAND": "-", "RSI METER": "-", "VOLUME DYNAMICS": "-", "QUANTITATIVE ACTION": "ERROR"}
    return pd.DataFrame(tech_results).T

df_tech = load_technical_data()

# ---------------------------------------------------------
# 3. [사이드바] 포트폴리오 파라미터 제어
# ---------------------------------------------------------
st.sidebar.markdown("### ⚙️ PORTFOLIO ENGINE")
target_cash_ratio = st.sidebar.slider("TARGET CASH WEIGHT (%)", 10, 40, 30) / 100.0
monthly_add = st.sidebar.number_input("MONTHLY INFLOW (KRW 10K)", min_value=0, max_value=2000, value=100, step=50) * 10000
exp_return = st.sidebar.slider("EXPECTED ANNUAL RETURN (%)", 5.0, 15.0, 9.5, 0.5) / 100.0
volatility = st.sidebar.slider("ANNUALIZED VOLATILITY (%)", 5.0, 25.0, 14.0, 1.0) / 100.0

def run_monte_carlo(initial, monthly, mu, sigma, years=7, sims=1000):
    np.random.seed(42)
    months = years * 12
    dt = 1 / 12
    paths = np.zeros((months + 1, sims))
    paths[0] = initial
    for t in range(1, months + 1):
        z = np.random.standard_normal(sims)
        paths[t] = paths[t - 1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z) + monthly
    prob = np.mean(paths[-1] >= initial * 2)
    return paths, prob, np.median(paths[-1])

paths, success_prob, median_final = run_monte_carlo(total_asset, monthly_add, exp_return, volatility)

# ---------------------------------------------------------
# 4. [상단 요약 KPI 카드 섹션]
# ---------------------------------------------------------
st.markdown("### 📊 EXECUTIVE SUMMARY & 7-YEAR TARGET TRACKING")
with st.container():
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("CURRENT AUM", f"{total_asset:,.0f} KRW")
    k2.metric("TARGET 2X (7Y)", f"{total_asset * 2:,.0f} KRW")
    k3.metric("PROBABILITY OF SUCCESS", f"{success_prob * 100:.1f} %")
    k4.metric("MEDIAN FINAL VALUE", f"{median_final:,.0f} KRW")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. [섹션 1] 퇴직연금 70% 룰 컴플라이언스
# ---------------------------------------------------------
st.markdown("### ⚖️ SECTION 1: RETIREMENT ACCOUNT 70% COMPLIANCE MONITOR")

irp_df = df_port[df_port["계좌"] == "퇴직연금(870)"]
irp_total = irp_df["평가금액"].sum()
irp_risk_asset = irp_df[irp_df["연금위험자산"] == True]["평가금액"].sum()
irp_risk_ratio = (irp_risk_asset / irp_total * 100) if irp_total > 0 else 0
irp_available_risk_buy = max(0, (irp_total * 0.70) - irp_risk_asset)
wt_cash = df_port[(df_port['계좌']=='위탁계좌') & (df_port['구분']=='현금')]['평가금액'].sum()

with st.container():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("IRP TOTAL AUM", f"{irp_total:,.0f} KRW")
    c2.metric("RISK ASSET RATIO", f"{irp_risk_ratio:.2f} %", f"HEADROOM: {max(0, 70.0 - irp_risk_ratio):.2f}%")
    c3.metric("IRP EQUITY CAPACITY", f"{irp_available_risk_buy:,.0f} KRW")
    c4.metric("BROKERAGE FREE CASH", f"{wt_cash:,.0f} KRW")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. [섹션 2] 다이나믹 리밸런싱 가이드
# ---------------------------------------------------------
st.markdown("### 🎯 SECTION 2: DYNAMIC REBALANCING & ASSET ALLOCATION")
current_cash = df_port[df_port["구분"] == "현금"]["평가금액"].sum()
target_cash_amount = total_asset * target_cash_ratio
deployable_cash = current_cash - target_cash_amount

st.markdown(f"""
* **TARGET CASH ALLOCATION:** `{target_cash_ratio * 100:.1f}%` (OPTIMAL RESERVE: `{target_cash_amount:,.0f} KRW`)
* **CURRENT CASH RESERVES:** `{current_cash:,.0f} KRW` (`{current_cash/total_asset*100:.1f}%`)
* **💡 DEPLOYABLE EXCESS CAPITAL:** **`{deployable_cash:,.0f} KRW`**
""")

remaining_ratio = 1.0 - target_cash_ratio
target_weights = {
    "반도체": 0.40 * remaining_ratio,
    "미국배당": 0.30 * remaining_ratio,
    "국내지수": 0.15 * remaining_ratio,
    "대체/채권": 0.10 * remaining_ratio,
    "현금": target_cash_ratio
}

sector_summary = df_port.groupby("구분")["평가금액"].sum().reset_index()
for sec in ["반도체", "미국배당", "국내지수", "대체/채권", "현금"]:
    if sec not in sector_summary["구분"].values:
        sector_summary = pd.concat([sector_summary, pd.DataFrame([{"구분": sec, "평가금액": 0.0}])], ignore_index=True)

sector_summary["CURRENT WEIGHT (%)"] = (sector_summary["평가금액"] / total_asset * 100).round(2)
sector_summary["TARGET WEIGHT (%)"] = sector_summary["구분"].map(target_weights) * 100
sector_summary["TARGET VALUE"] = total_asset * sector_summary["구분"].map(target_weights)
sector_summary["REBALANCE DELTA"] = sector_summary["TARGET VALUE"] - sector_summary["평가금액"]

def get_action_text(diff):
    if diff > 1000000: return f"🟢 BUY +{diff:,.0f} KRW"
    elif diff < -1000000: return f"🔴 REDUCE {abs(diff):,.0f} KRW"
    else: return "⚪ OPTIMAL WEIGHT"

sector_summary["EXECUTION MANDATE"] = sector_summary["REBALANCE DELTA"].apply(get_action_text)

display_rebal = sector_summary[["구분", "CURRENT WEIGHT (%)", "TARGET WEIGHT (%)", "REBALANCE DELTA", "EXECUTION MANDATE"]].copy()
st.markdown(display_rebal.to_html(classes="custom-table", index=False, escape=False), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 7. [섹션 3] 기술적 지표 매매 제안
# ---------------------------------------------------------
st.markdown("### 🔍 SECTION 3: 5-FACTOR QUANTITATIVE TECHNICAL SCREENING")
st.markdown("Multi-factor scoring: `20-Day MA` + `Bollinger Lower Band` + `RSI Oversold` + `Volume Dynamics`.")
st.markdown(df_tech.reset_index().rename(columns={"index": "ASSET/TICKER"}).to_html(classes="custom-table", index=False, escape=False), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 8. [섹션 4] 손실 종목 물타기 유효성 진단
# ---------------------------------------------------------
st.markdown("### 🛡️ SECTION 4: DRAWDOWN & AVERAGING-DOWN EVALUATION")

loss_stocks = df_port[df_port["구분"] == "반도체"].groupby("종목명")[["매입금액", "평가금액"]].sum().reset_index()
loss_stocks["손익금액"] = loss_stocks["평가금액"] - loss_stocks["매입금액"]
loss_stocks["손익률(%)"] = np.where(loss_stocks["매입금액"] > 0, (loss_stocks["손익금액"] / loss_stocks["매입금액"]) * 100, 0.0)

def evaluate_averaging_down(row):
    loss_pct = row["손익률(%)"]
    if loss_pct <= -40:
        return "⚠️ HIGH RISK (SEVERE DRAWDOWN)", "Avoid aggressive scaling. Allocate fresh liquidity to diversified equities."
    elif -40 < loss_pct <= -20:
        return "🔍 CONDITIONAL (SCALE-IN)", "Verify technical support at MA20 / BB Lower before tranche allocation."
    else:
        return "🟢 ATTRACTIVE (ACCUMULATE)", "Short-term retracement provides valid averaging opportunity."

eval_results = []
for _, row in loss_stocks.iterrows():
    status, advice = evaluate_averaging_down(row)
    eval_results.append({
        "ASSET NAME": row["종목명"],
        "TOTAL COST BASIS": f"{row['매입금액']:,.0f} KRW",
        "MARKET VALUE": f"{row['평가금액']:,.0f} KRW",
        "RETURN RATE": f"{loss_stocks.loc[loss_stocks['종목명']==row['종목명'], '손익률(%)'].values[0]:.2f} %",
        "DIAGNOSTIC STATUS": status,
        "STRATEGIC ADVISORY": advice
    })

eval_df = pd.DataFrame(eval_results)
if not eval_df.empty:
    st.markdown(eval_df.to_html(classes="custom-table", index=False, escape=False), unsafe_allow_html=True)
else:
    st.info("NO SEMICONDUCTOR DRAWDOWN TARGETS FLAGGED.")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 9. [섹션 5] 몬테카를로 시뮬레이션
# ---------------------------------------------------------
st.markdown("### 📊 SECTION 5: MONTE CARLO 7-YEAR WEALTH PROJECTION (1,000 SIMULATIONS)")

months_x = np.arange(paths.shape[0]) / 12
p10 = np.percentile(paths, 10, axis=1)
p50 = np.percentile(paths, 50, axis=1)
p90 = np.percentile(paths, 90, axis=1)

fig = go.Figure()
fig.add_trace(go.Scatter(x=months_x, y=p90, name="OPTIMISTIC (P90)", line=dict(color="#3fb950", dash="dot", width=2)))
fig.add_trace(go.Scatter(x=months_x, y=p50, name="MEDIAN BASELINE (P50)", line=dict(color="#58a6ff", width=3)))
fig.add_trace(go.Scatter(x=months_x, y=p10, name="CONSERVATIVE (P10)", line=dict(color="#8b949e", dash="dot", width=2)))
fig.add_hline(y=total_asset * 2, line_dash="dash", line_color="#f85149", annotation_text="TARGET WEALTH 2X LINE", annotation_font=dict(size=14, color="#f85149"))

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="#161b22",
    plot_bgcolor="#161b22",
    xaxis=dict(title="INVESTMENT HORIZON (YEARS)", gridcolor="#30363d", title_font=dict(color="#c9d1d9")),
    yaxis=dict(title="PORTFOLIO VALUE (KRW)", gridcolor="#30363d", title_font=dict(color="#c9d1d9")),
    height=480,
    margin=dict(l=60, r=20, t=30, b=30),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#c9d1d9")),
    font=dict(color="#c9d1d9")
)
st.plotly_chart(fig, use_container_width=True)
