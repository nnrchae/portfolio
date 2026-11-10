import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
from datetime import datetime, timedelta
import plotly.graph_objects as go
import re

# ---------------------------------------------------------
# 0. 페이지 설정 및 프리미엄 와인/버건디 테마 CSS
# ---------------------------------------------------------
st.set_page_config(page_title="프리미엄 자산관리 & 동적 리밸런싱 터미널", layout="wide")

st.markdown("""
<style>
    .main {
        background-color: #f7f6f2;
        color: #222222;
    }
    h1 {
        font-size: 2.4rem !important;
        font-weight: 800 !important;
        color: #7a1c2e !important;
        letter-spacing: -0.5px;
    }
    h2, h3, .section-title {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #4a121d !important;
        border-left: 6px solid #7a1c2e;
        padding-left: 12px;
        margin-top: 35px;
        margin-bottom: 15px;
    }
    p, li, span, label, div {
        font-size: 1.15rem !important;
        color: #333333 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #1a1a1a !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        color: #555555 !important;
    }
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #ffffff;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .custom-table th {
        background-color: #7a1c2e !important;
        color: white !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        padding: 14px 16px !important;
        text-align: left;
    }
    .custom-table td {
        font-size: 1.12rem !important;
        padding: 14px 16px !important;
        color: #222222 !important;
        border-bottom: 1px solid #e5e7eb !important;
        white-space: normal !important;
        word-break: break-all !important;
        line-height: 1.5 !important;
    }
    .custom-table tr:hover {
        background-color: #fdfbf7 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("💼 프리미엄 자산관리 및 5대 지표 복합 분석 터미널")
st.markdown(f"**📅 기준일:** {datetime.now().strftime('%Y-%m-%d')} &nbsp;|&nbsp; **🎯 운용 목표:** 7년 내 순자산 2배 증식 & 최신 잔고 기본 고정")
st.markdown("<hr style='border: 1px solid #dcd7d0; margin-top: 10px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. [동적 데이터 입력 레이어] 최신 잔고 데이터 기본 고정
# ---------------------------------------------------------
st.markdown("### 📥 실시간 자산 현황 데이터 입력")
st.markdown("아래 입력창에 최신 잔고 데이터가 기본으로 반영되어 있습니다. 필요시 수정하여 사용할 수 있습니다.")

default_raw_data = """예수금 340-375-915-01 예수금 154,079,041
예수금 363-810-976-01 예수금 345,478
예수금 376-640-119-01 예수금 1,881,569
주식 340-375-915-01 SK하이닉스 -38.17 -6,988,810 10 18,308,810 11,320,000
주식 340-375-915-01 삼성전자 -22.5 -16,442,530 300 243,508 73,052,530 56,610,000
주식 363-810-976-01 TIGER 미국배당다우존스타겟데일리커버드콜 -2.22 -830,885 3,683 10,161 37,421,490 36,590,605
주식 376-640-119-01 TIGER 미국배당다우존스타겟데일리커버드콜 -5.24 -390,760 711 10,485 7,454,545 7,063,785
주식 376-640-119-01 SOL AI반도체TOP2플러스 -54.53 -70,110,364 5,000 25,712 128,560,364 58,450,000
퇴직연금 870-126-269-01 TIGER 미국배당다우존스타겟데일리커버드콜 -2.21 -225 10 10,160 9,935
퇴직연금 870-126-269-01 PLUS 코스피50 -37.76 -963,395 270 2,551,400 1,588,005
퇴직연금 870-126-269-01 TIGER 미국배당다우존스타겟데일리커버드콜 1.08 533,360 5,011 9,828 49,250,925 49,784,285
퇴직연금 870-126-269-01 TIGER 200 -8.97 -620,740 800 8,646 6,917,140 6,296,400
퇴직연금 870-126-269-01 ACE KRX금현물 -22.23 -704,660 100 31,702 3,170,160 2,465,500
퇴직연금 870-126-269-01 SOL AI반도체TOP2플러스 -47.61 -57,708,530 5,433 22,312 121,220,300 63,511,770
퇴직연금 870-126-269-01 PLUS 코스피50 -38.53 -18,429,195 5,000 9,567 47,836,695 29,407,500
퇴직연금 870-126-269-01 ACE 미국30년국채액티브 2.45 20,960 1,000 855 854,540 875,500
퇴직연금 870-126-269-01 현금자산 0 0 72,311,119 72,311,119"""

user_raw_input = st.text_area("📋 자산 현황 텍스트 (기본 고정됨):", value=default_raw_data, height=150)

def parse_user_asset_text(raw_text):
    lines = raw_text.strip().split("\n")
    parsed_rows = []
    for line in lines:
        if not line.strip() or ("구분" in line and "종목명" in line): continue
        tokens = line.strip().split()
        if len(tokens) < 2: continue
        gubun = tokens[0]
        
        account = "기타계좌"
        acc_idx = -1
        for i, t in enumerate(tokens):
            if re.match(r'\d{3}-\d+-\d+', t):
                account = t
                acc_idx = i
                break
        if acc_idx == -1: continue
        
        remainder_tokens = tokens[acc_idx+1:]
        stock_name_parts, numeric_tokens = [], []
        is_numeric_started = False
        for t in remainder_tokens:
            clean_t = t.replace(',', '').replace('%', '')
            try:
                float(clean_t)
                is_numeric_started = True
                numeric_tokens.append(clean_t)
            except ValueError:
                if not is_numeric_started: stock_name_parts.append(t)
                else: numeric_tokens.append(clean_t)
                    
        stock_name = " ".join(stock_name_parts) if stock_name_parts else "현금성자산"
        if "예수금" in gubun or not stock_name_parts: stock_name = "예수금/현금"
            
        float_nums = [float(nt) for nt in numeric_tokens if nt.replace('.','',1).isdigit() or (nt.startswith('-') and nt[1:].replace('.','',1).isdigit())]
        eval_amount = float_nums[-1] if len(float_nums) >= 1 else 0.0
        buy_amount = float_nums[-2] if len(float_nums) >= 2 else eval_amount
            
        account_label = "위탁계좌" if "340" in account or "363" in account or "376" in account else "퇴직연금(870)"
        
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
            "평가금액": eval_amount,
            "연금위험자산": is_irp_risk
        })
    return pd.DataFrame(parsed_rows)

df_port = parse_user_asset_text(user_raw_input)
if df_port.empty or df_port["평가금액"].sum() == 0:
    st.warning("⚠️ 입력된 텍스트에서 자산 데이터를 읽어오지 못했습니다.")
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
            ma20_status = "🟢 20일선 아래 (싼 구간)" if cur_price < ma20 else "🔴 20일선 위 (비싼 구간)"
            std20 = pdf['Close'].rolling(20).std().iloc[-1]
            bb_lower = ma20 - (2 * std20)
            bb_status = "🟢 볼린저 하단 (과매도)" if cur_price <= bb_lower * 1.02 else "⚪ 밴드 내부 정상"
            delta = pdf['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            cur_rsi = (100 - (100 / (1 + rs))).iloc[-1]
            rsi_status = f"🟢 RSI {cur_rsi:.1f} (과매도 30근처)" if cur_rsi <= 35 else (f"🔴 RSI {cur_rsi:.1f} (과열)" if cur_rsi >= 65 else f"⚪ RSI {cur_rsi:.1f} (중립)")
            pdf['TradeValue'] = pdf['Close'] * pdf['Volume']
            vol_5 = pdf['TradeValue'].rolling(5).mean().iloc[-1]
            vol_20 = pdf['TradeValue'].rolling(20).mean().iloc[-1]
            vol_status = "🟢 거래대금 유입" if vol_5 > vol_20 * 1.2 else "⚪ 거래대금 잠잠"
            score = 0
            if cur_price < ma20: score += 1
            if cur_price <= bb_lower * 1.02: score += 1
            if cur_rsi <= 35: score += 1
            if vol_5 > vol_20 * 1.2: score += 1
            action = "🟢 [적극 매수 타이밍]" if score >= 3 else ("🟡 [분할 매수 관망]" if score == 2 else "⚪ [보유 및 홀딩]")

            tech_results[name] = {
                "현재가": f"{int(cur_price):,}원",
                "20일선 진단": ma20_status,
                "볼린저밴드": bb_status,
                "RSI 진단": rsi_status,
                "거래대금": vol_status,
                "종합 매매 제안": action
            }
        except Exception:
            tech_results[name] = {"현재가": "조회 불가", "20일선 진단": "-", "볼린저밴드": "-", "RSI 진단": "-", "거래대금": "-", "종합 매매 제안": "데이터 오류"}
    return pd.DataFrame(tech_results).T

df_tech = load_technical_data()

# ---------------------------------------------------------
# 3. [사이드바] 슬라이더 및 동적 리밸런싱 파라미터 제어
# ---------------------------------------------------------
st.sidebar.markdown("### ⚙️ 투자 전략 및 시뮬레이션 설정")
target_cash_ratio = st.sidebar.slider("목표 현금 비중 (%)", 10, 40, 30) / 100.0
monthly_add = st.sidebar.number_input("월 추가 적립금액 (만원)", min_value=0, max_value=2000, value=100, step=50) * 10000
exp_return = st.sidebar.slider("포트폴리오 연 기대수익률 (%)", 5.0, 15.0, 9.5, 0.5) / 100.0
volatility = st.sidebar.slider("연간 변동성 (%)", 5.0, 25.0, 14.0, 1.0) / 100.0

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
st.markdown("### 📊 포트폴리오 총괄 요약 (Executive Summary)")
with st.container():
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("현재 총 순자산 (AUM)", f"{total_asset:,.0f} 원")
    k2.metric("7년 후 목표 자산 (2배)", f"{total_asset * 2:,.0f} 원")
    k3.metric("7년 내 목표 달성 확률", f"{success_prob * 100:.1f} %")
    k4.metric("7년 후 예상 중위 자산", f"{median_final:,.0f} 원")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. [섹션 1] 퇴직연금 70% 룰 검증 패널
# ---------------------------------------------------------
st.markdown("### ⚖️ 섹션 1: 퇴직연금(870) 법적 한도(위험자산 70%) 컴플라이언스 진단")

irp_df = df_port[df_port["계좌"] == "퇴직연금(870)"]
irp_total = irp_df["평가금액"].sum()
irp_risk_asset = irp_df[irp_df["연금위험자산"] == True]["평가금액"].sum()
irp_risk_ratio = (irp_risk_asset / irp_total * 100) if irp_total > 0 else 0
irp_available_risk_buy = max(0, (irp_total * 0.70) - irp_risk_asset)
wt_cash = df_port[(df_port['계좌']=='위탁계좌') & (df_port['구분']=='현금')]['평가금액'].sum()

with st.container():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("퇴직연금 총 평가액", f"{irp_total:,.0f} 원")
    c2.metric("현재 위험자산 비중", f"{irp_risk_ratio:.2f} %", f"한도까지 {max(0, 70.0 - irp_risk_ratio):.2f}%p 여유")
    c3.metric("연금 내 주식 추가매수 한도", f"{irp_available_risk_buy:,.0f} 원")
    c4.metric("위탁계좌 가용 현금", f"{wt_cash:,.0f} 원")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. [섹션 2] 슬라이더 연동 실시간 자산 배분 및 리밸런싱 처방 패널
# ---------------------------------------------------------
st.markdown("### 🎯 섹션 2: 목표 현금 비중 슬라이더 연동 리밸런싱 가이드")
current_cash = df_port[df_port["구분"] == "현금"]["평가금액"].sum()
target_cash_amount = total_asset * target_cash_ratio
deployable_cash = current_cash - target_cash_amount

st.markdown(f"""
* **설정된 목표 현금 비중:** `{target_cash_ratio * 100:.1f}%` (적정 보유 현금: `{target_cash_amount:,.0f}원`)
* **현재 총 현금 보유액:** `{current_cash:,.0f}원` (`{current_cash/total_asset*100:.1f}%`)
* **💡 투자 집행 가능 초과 현금:** **`{deployable_cash:,.0f}원`** *(이 금액을 슬라이더 비중에 맞춰 시장에 투입하거나 확보해야 합니다)*
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

sector_summary["현재비중(%)"] = (sector_summary["평가금액"] / total_asset * 100).round(2)
sector_summary["목표비중(%)"] = sector_summary["구분"].map(target_weights) * 100
sector_summary["목표금액"] = total_asset * sector_summary["구분"].map(target_weights)
sector_summary["조정필요금액"] = sector_summary["목표금액"] - sector_summary["평가금액"]

def get_action_text(diff):
    if diff > 1000000: return f"🟢 +{diff:,.0f}원 추가 매수 권장"
    elif diff < -1000000: return f"🔴 {abs(diff):,.0f}원 비중 축소 (현금화)"
    else: return "⚪ 목표 비중 적정"

sector_summary["처방 액션"] = sector_summary["조정필요금액"].apply(get_action_text)

display_rebal = sector_summary[["구분", "현재비중(%)", "목표비중(%)", "조정필요금액", "처방 액션"]].copy()
st.markdown(display_rebal.to_html(classes="custom-table", index=False, escape=False), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 7. [섹션 3] 5대 기술적 지표 복합 매매 제안 패널
# ---------------------------------------------------------
st.markdown("### 🔍 섹션 3: 5대 기술적 지표 복합 로직 기반 종목별 매매 제안")
st.markdown("`20일 이동평균선` + `볼린저밴드 하단 울타리` + `RSI 과매도(30근처)` + `거래대금 유입 여부` 스코어링 결과입니다.")
st.markdown(df_tech.reset_index().rename(columns={"index": "종목명"}).to_html(classes="custom-table", index=False, escape=False), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 8. [섹션 4] 물타기 유효성 진단 패널
# ---------------------------------------------------------
st.markdown("### 🛡️ 섹션 4: 주요 손실 종목 '물타기(평단가 낮추기)' 유효성 진단")

loss_stocks = df_port[df_port["구분"] == "반도체"].groupby("종목명")[["매입금액", "평가금액"]].sum().reset_index()
loss_stocks["손익금액"] = loss_stocks["평가금액"] - loss_stocks["매입금액"]
loss_stocks["손익률(%)"] = np.where(loss_stocks["매입금액"] > 0, (loss_stocks["손익금액"] / loss_stocks["매입금액"]) * 100, 0.0)

def evaluate_averaging_down(row):
    loss_pct = row["손익률(%)"]
    if loss_pct <= -40:
        return "⚠️ 주의 (비중 과다 & 깊은 손실)", "무분별한 물타기 지양. 신규 현금은 현대차나 미국배당 등 타 자산으로 분산하는 것이 유리함."
    elif -40 < loss_pct <= -20:
        return "🔍 조건부 유효 (분할 접근)", "20일선 및 볼린저 하단 지지 여부를 확인하며 소액으로만 분할 접근 권장."
    else:
        return "🟢 유효 (적극 매수 기회)", "단기 조정 구간이므로 분할 매수로 평단가 낮추기 유효."

eval_results = []
for _, row in loss_stocks.iterrows():
    status, advice = evaluate_averaging_down(row)
    eval_results.append({
        "종목명": row["종목명"],
        "총 매입금액": f"{row['매입금액']:,.0f} 원",
        "평가금액": f"{row['평가금액']:,.0f} 원",
        "현재 손익률": f"{loss_stocks.loc[loss_stocks['종목명']==row['종목명'], '손익률(%)'].values[0]:.2f} %",
        "물타기 진단": status,
        "맞춤 처방 가이드": advice
    })

eval_df = pd.DataFrame(eval_results)
if not eval_df.empty:
    st.markdown(eval_df.to_html(classes="custom-table", index=False, escape=False), unsafe_allow_html=True)
else:
    st.info("현재 진단할 반도체 손실 종목이 없습니다.")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 9. [섹션 5] 7년 자산 성장 시뮬레이션 차트
# ---------------------------------------------------------
st.markdown("### 📊 섹션 5: 향후 7년 자산 증식 몬테카를로 시뮬레이션 궤적")

months_x = np.arange(paths.shape[0]) / 12
p10 = np.percentile(paths, 10, axis=1)
p50 = np.percentile(paths, 50, axis=1)
p90 = np.percentile(paths, 90, axis=1)

fig = go.Figure()
fig.add_trace(go.Scatter(x=months_x, y=p90, name="낙관적 시나리오 (상위 10%)", line=dict(color="#7a1c2e", dash="dot", width=2.5)))
fig.add_trace(go.Scatter(x=months_x, y=p50, name="기본 시나리오 (중위값 P50)", line=dict(color="#0d652d", width=3.5)))
fig.add_trace(go.Scatter(x=months_x, y=p10, name="보수적 시나리오 (하위 10%)", line=dict(color="#5f6368", dash="dot", width=2.5)))
fig.add_hline(y=total_asset * 2, line_dash="dash", line_color="#b0a89f", annotation_text="목표 순자산 2배선", annotation_font=dict(size=15, color="#7a1c2e"))

fig.update_layout(
    template="plotly_white",
    xaxis=dict(title="투자 경과 기간 (년)", title_font=dict(size=16, color="#222222"), tickfont=dict(size=15, color="#333333")),
    yaxis=dict(title="예상 총 자산 (KRW)", title_font=dict(size=16, color="#222222"), tickfont=dict(size=15, color="#333333")),
    height=500,
    margin=dict(l=50, r=20, t=30, b=30),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=15, color="#222222")),
    font=dict(size=15)
)
st.plotly_chart(fig, use_container_width=True)
