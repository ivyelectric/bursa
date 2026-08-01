"""
IVY TRADING — Market analysis terminal / Terminal de analiza bursiera
======================================================================
Local run:   streamlit run app.py
Free deploy: share.streamlit.io
"""

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Ivy Trading", page_icon="◆", layout="wide")

# ============================================================
# BRAND — Ivy palette
# ============================================================
INK = "#0E1524"        # background (derived from Ivy navy)
NAVY = "#1B2A4A"       # Ivy navy — panels
LINE = "#2A3A5C"       # borders
TEXT = "#EAEEF6"
MUTED = "#8B96AD"
BLUE = "#4A8FE0"       # accent (lightened Ivy blue #2E5FA3)
GOLD = "#D9A441"       # secondary accent
UP = "#3DD68C"
DOWN = "#F26D6D"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
h1, h2, h3 {{ font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.01em; }}
.block-container {{ padding-top: 1.4rem; max-width: 1240px; }}

.brand {{ display:flex; align-items:baseline; gap:.8rem;
  border-bottom:1px solid {LINE}; padding-bottom:1rem; }}
.brand .logo {{ font-family:'Space Grotesk',sans-serif; font-weight:700;
  font-size:1.9rem; color:{TEXT}; }}
.brand .logo span {{ color:{BLUE}; }}
.brand .tag {{ font-family:'IBM Plex Mono',monospace; font-size:.72rem;
  color:{MUTED}; text-transform:uppercase; letter-spacing:.14em; }}

.tickerband {{ display:flex; flex-wrap:wrap; background:{NAVY};
  border:1px solid {LINE}; border-radius:10px; margin:1rem 0 1.2rem; overflow:hidden; }}
.tick {{ flex:1 1 130px; padding:.75rem 1rem; border-right:1px solid {LINE};
  font-family:'IBM Plex Mono',monospace; }}
.tick:last-child {{ border-right:none; }}
.tick .sym {{ font-size:.7rem; color:{MUTED}; letter-spacing:.12em; }}
.tick .px {{ font-size:1.2rem; font-weight:600; color:{TEXT}; margin:.1rem 0; }}
.tick .chg {{ font-size:.78rem; font-weight:500; }}

.verdict {{ background:{NAVY}; border:1px solid {LINE}; border-left:3px solid {BLUE};
  border-radius:8px; padding:.8rem 1rem; font-size:.86rem; color:{TEXT}; margin-bottom:.7rem; }}
.verdict.good {{ border-left-color:{UP}; }}
.verdict.warn {{ border-left-color:{DOWN}; }}
.verdict .k {{ font-family:'IBM Plex Mono',monospace; font-size:.68rem; color:{MUTED};
  text-transform:uppercase; letter-spacing:.12em; display:block; margin-bottom:.2rem; }}

.stat {{ background:{NAVY}; border:1px solid {LINE}; border-radius:8px;
  padding:.7rem .9rem; margin-bottom:.6rem; }}
.stat .k {{ font-family:'IBM Plex Mono',monospace; font-size:.66rem; color:{MUTED};
  text-transform:uppercase; letter-spacing:.1em; }}
.stat .v {{ font-family:'IBM Plex Mono',monospace; font-size:1.05rem;
  font-weight:600; color:{TEXT}; margin-top:.15rem; }}

.stTabs [data-baseweb="tab-list"] {{ gap:.3rem; border-bottom:1px solid {LINE}; }}
.stTabs [data-baseweb="tab"] {{ font-family:'IBM Plex Mono',monospace; font-size:.78rem;
  letter-spacing:.06em; text-transform:uppercase; color:{MUTED}; padding:.55rem 1rem; }}
.stTabs [aria-selected="true"] {{ color:{BLUE} !important; border-bottom:2px solid {BLUE}; }}

.stButton > button, .stDownloadButton > button {{
  font-family:'IBM Plex Mono',monospace; text-transform:uppercase; letter-spacing:.08em;
  font-size:.76rem; font-weight:600; background:{BLUE}; color:#fff; border:none;
  border-radius:8px; padding:.55rem 1.3rem; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ background:#5E9FEA; color:#fff; }}

[data-testid="stDataFrame"] {{ border:1px solid {LINE}; border-radius:10px; }}
[data-testid="stSidebar"] {{ border-right:1px solid {LINE}; }}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
  font-family:'IBM Plex Mono',monospace !important; font-size:.76rem !important;
  text-transform:uppercase; letter-spacing:.12em; color:{MUTED} !important; }}

.legal {{ font-size:.72rem; color:{MUTED}; border-top:1px solid {LINE};
  padding-top:1rem; margin-top:2rem; line-height:1.5; }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# I18N — RO / EN
# ============================================================
T = {
"ro": {
  "tag": "Analiza piete · S&P 500",
  "lang": "Limba / Language",
  "watchlist": "Watchlist",
  "presets": "Liste predefinite",
  "custom": "Tickere proprii (virgula)",
  "period": "Perioada grafice",
  "tabs": ["Piata", "Screener", "Semnale tehnice", "Analiza actiune"],
  "dca_title": "Termen lung — e piata la reducere?",
  "dca_good": "Corectie de peste 10% fata de maxim — istoric, moment favorabil de suplimentat DCA.",
  "dca_warn": "Sub media de 200 zile — pret sub trend, de urmarit.",
  "dca_norm": "Trend normal — continua DCA lunar standard.",
  "vs_max": "vs max 52 sapt",
  "scr_title": "Screener fundamental",
  "scr_run": "Ruleaza screener",
  "scr_filters": "Filtre fundamentale",
  "scr_note": "Un P/E mic nu inseamna automat 'ieftin' — verifica de ce e mic.",
  "scr_empty": "Nu s-au putut incarca date pentru watchlist.",
  "scr_pass": "TRECE",
  "download": "Descarca CSV",
  "max_pe": "P/E maxim", "max_fpe": "Forward P/E maxim", "max_peg": "PEG maxim",
  "max_pb": "P/B maxim", "min_div": "Dividend minim (%)", "min_marja": "Marja profit minima (%)",
  "min_roe": "ROE minim (%)", "max_de": "Datorii/Capital maxim (D/E)", "max_beta": "Beta maxim",
  "min_cap": "Capitalizare minima (mld $)",
  "sig_title": "Semnale tehnice pe watchlist",
  "sig_run": "Cauta semnale",
  "sig_settings": "Setari semnale",
  "sig_empty": "Niciun semnal tehnic notabil azi.",
  "sig_note": "Semnalele tehnice sunt indicii, nu predictii.",
  "rsi_low": "RSI supravandut sub", "rsi_high": "RSI supracumparat peste",
  "ma_pair": "Pereche medii mobile", "use_macd": "Include incrucisari MACD",
  "use_52w": "Include apropiere de min/max 52 sapt", "use_vol": "Include volum neobisnuit (>2x medie)",
  "oversold": "supravandut", "overbought": "supracumparat",
  "near_low": "la <5% de minim 52 sapt", "near_high": "la <2% de maxim 52 sapt",
  "vol_spike": "volum >2x media", "macd_up": "MACD incrucisare in sus", "macd_dn": "MACD incrucisare in jos",
  "an_title": "Analiza detaliata pe o actiune",
  "an_pick": "Alege actiunea",
  "price": "Pret", "chg_day": "Variatie zi", "pe": "P/E", "fpe": "Fwd P/E",
  "div": "Dividend", "cap": "Capitalizare", "beta": "Beta", "range52": "Interval 52 sapt",
  "sector": "Sector", "target": "Tinta analisti",
  "signals_now": "Semnale curente",
  "no_data": "Date indisponibile pentru acest ticker.",
  "cols": {"t":"Ticker","p":"Pret ($)","pe":"P/E","fpe":"Fwd P/E","peg":"PEG","pb":"P/B",
           "div":"Div (%)","m":"Marja (%)","roe":"ROE (%)","de":"D/E","b":"Beta",
           "cap":"Cap (mld$)","sec":"Sector","v":"Verdict","sig":"Semnale"},
  "legal": ("Date: Yahoo Finance, intarziere ~15 min, cache 1 ora. Acest site are scop strict "
            "informativ si educational. Nu constituie consultanta financiara, recomandare de "
            "investitii sau oferta de servicii de investitii. Investitiile la bursa implica risc "
            "de pierdere a capitalului. Performanta trecuta nu garanteaza rezultate viitoare."),
},
"en": {
  "tag": "Market analysis · S&P 500",
  "lang": "Limba / Language",
  "watchlist": "Watchlist",
  "presets": "Preset lists",
  "custom": "Custom tickers (comma-separated)",
  "period": "Chart period",
  "tabs": ["Market", "Screener", "Technical signals", "Stock analysis"],
  "dca_title": "Long term — is the market on sale?",
  "dca_good": "Over 10% below the high — historically a favourable moment to top up DCA.",
  "dca_warn": "Below the 200-day average — price under trend, worth watching.",
  "dca_norm": "Normal trend — continue standard monthly DCA.",
  "vs_max": "vs 52-wk high",
  "scr_title": "Fundamental screener",
  "scr_run": "Run screener",
  "scr_filters": "Fundamental filters",
  "scr_note": "A low P/E doesn't automatically mean 'cheap' — check why it's low.",
  "scr_empty": "Could not load data for the watchlist.",
  "scr_pass": "PASS",
  "download": "Download CSV",
  "max_pe": "Max P/E", "max_fpe": "Max forward P/E", "max_peg": "Max PEG",
  "max_pb": "Max P/B", "min_div": "Min dividend (%)", "min_marja": "Min profit margin (%)",
  "min_roe": "Min ROE (%)", "max_de": "Max debt/equity (D/E)", "max_beta": "Max beta",
  "min_cap": "Min market cap ($bn)",
  "sig_title": "Technical signals on watchlist",
  "sig_run": "Scan for signals",
  "sig_settings": "Signal settings",
  "sig_empty": "No notable technical signals today.",
  "sig_note": "Technical signals are clues, not predictions.",
  "rsi_low": "RSI oversold below", "rsi_high": "RSI overbought above",
  "ma_pair": "Moving average pair", "use_macd": "Include MACD crossovers",
  "use_52w": "Include 52-wk high/low proximity", "use_vol": "Include unusual volume (>2x avg)",
  "oversold": "oversold", "overbought": "overbought",
  "near_low": "within 5% of 52-wk low", "near_high": "within 2% of 52-wk high",
  "vol_spike": "volume >2x average", "macd_up": "MACD bullish crossover", "macd_dn": "MACD bearish crossover",
  "an_title": "Single stock deep dive",
  "an_pick": "Pick a stock",
  "price": "Price", "chg_day": "Day change", "pe": "P/E", "fpe": "Fwd P/E",
  "div": "Dividend", "cap": "Market cap", "beta": "Beta", "range52": "52-wk range",
  "sector": "Sector", "target": "Analyst target",
  "signals_now": "Current signals",
  "no_data": "No data available for this ticker.",
  "cols": {"t":"Ticker","p":"Price ($)","pe":"P/E","fpe":"Fwd P/E","peg":"PEG","pb":"P/B",
           "div":"Div (%)","m":"Margin (%)","roe":"ROE (%)","de":"D/E","b":"Beta",
           "cap":"Cap ($bn)","sec":"Sector","v":"Verdict","sig":"Signals"},
  "legal": ("Data: Yahoo Finance, ~15 min delayed, cached for 1 hour. This site is for "
            "information and education only. It does not constitute financial advice, an "
            "investment recommendation or an offer of investment services. Stock market "
            "investing involves risk of capital loss. Past performance does not guarantee "
            "future results."),
},
}

# ============================================================
# PRESET WATCHLISTS
# ============================================================
PRESETS = {
    "Mega Tech": ["AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","AVGO"],
    "Financials": ["JPM","BAC","WFC","GS","MS","V","MA","AXP","BLK"],
    "Healthcare": ["UNH","JNJ","LLY","PFE","MRK","ABBV","TMO","ABT"],
    "Consumer": ["PG","KO","PEP","WMT","COST","HD","MCD","NKE","SBUX"],
    "Energy": ["XOM","CVX","COP","SLB","EOG","OXY"],
    "Industrials": ["CAT","BA","GE","HON","UNP","LMT","DE"],
    "Dividend": ["KO","PG","JNJ","PEP","MCD","MMM","T","VZ","O","XOM"],
    "Semiconductors": ["NVDA","AMD","INTC","AVGO","QCOM","TXN","MU","AMAT"],
}
DCA_ETFS = ["SPY", "VOO", "QQQ", "DIA", "IWM"]

# ============================================================
# DATA
# ============================================================
@st.cache_data(ttl=3600, show_spinner=False)
def get_history(ticker: str, period: str = "1y"):
    try:
        df = yf.Ticker(ticker).history(period=period)
        return df if not df.empty else None
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info
    except Exception:
        return {}

def calc_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - 100 / (1 + rs)

def calc_macd(prices: pd.Series):
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def norm_div(info: dict) -> float:
    d = info.get("dividendYield") or 0
    return d * 100 if d < 1 else d

# ============================================================
# HEADER + LANGUAGE
# ============================================================
with st.sidebar:
    lang = st.radio("Limba / Language", ["Română", "English"], horizontal=True)
L = T["ro" if lang == "Română" else "en"]
C = L["cols"]

st.markdown(f"""
<div class="brand">
  <div class="logo">IVY<span>◆</span>TRADING</div>
  <div class="tag">{L['tag']} · {datetime.now():%d.%m.%Y}</div>
</div>
""", unsafe_allow_html=True)

# Ticker band
etf_data = {e: get_history(e) for e in DCA_ETFS}
ticks = ""
for etf, df in etf_data.items():
    if df is None or len(df) < 2:
        continue
    pret, prev = df["Close"].iloc[-1], df["Close"].iloc[-2]
    chg = (pret / prev - 1) * 100
    cul, sag = (UP, "▲") if chg >= 0 else (DOWN, "▼")
    ticks += (f'<div class="tick"><div class="sym">{etf}</div>'
              f'<div class="px">${pret:,.2f}</div>'
              f'<div class="chg" style="color:{cul}">{sag} {chg:+.2f}%</div></div>')
st.markdown(f'<div class="tickerband">{ticks}</div>', unsafe_allow_html=True)

# ============================================================
# SIDEBAR — watchlist + filters
# ============================================================
with st.sidebar:
    st.header(L["watchlist"])
    chosen = st.multiselect(L["presets"], list(PRESETS.keys()), default=["Mega Tech", "Financials"])
    extra = st.text_area(L["custom"], value="", height=70)
    watchlist = sorted({t for p in chosen for t in PRESETS[p]}
                       | {t.strip().upper() for t in extra.split(",") if t.strip()})

    period = st.select_slider(L["period"], options=["6mo", "1y", "2y", "5y"], value="1y")

    st.header(L["scr_filters"])
    max_pe = st.slider(L["max_pe"], 5, 60, 25)
    max_fpe = st.slider(L["max_fpe"], 5, 60, 25)
    max_peg = st.slider(L["max_peg"], 0.5, 4.0, 2.0, 0.1)
    max_pb = st.slider(L["max_pb"], 1.0, 20.0, 8.0, 0.5)
    min_div = st.slider(L["min_div"], 0.0, 6.0, 0.0, 0.5)
    min_marja = st.slider(L["min_marja"], 0, 40, 8)
    min_roe = st.slider(L["min_roe"], 0, 40, 10)
    max_de = st.slider(L["max_de"], 0.0, 5.0, 2.5, 0.1)
    max_beta = st.slider(L["max_beta"], 0.5, 3.0, 2.0, 0.1)
    min_cap = st.slider(L["min_cap"], 0, 500, 10)

    st.header(L["sig_settings"])
    rsi_jos = st.slider(L["rsi_low"], 15, 40, 30)
    rsi_sus = st.slider(L["rsi_high"], 60, 90, 70)
    ma_pair = st.selectbox(L["ma_pair"], ["20/50", "50/200"], index=1)
    use_macd = st.checkbox(L["use_macd"], value=True)
    use_52w = st.checkbox(L["use_52w"], value=True)
    use_vol = st.checkbox(L["use_vol"], value=False)

ma_fast, ma_slow = (20, 50) if ma_pair == "20/50" else (50, 200)

# ============================================================
# TABS
# ============================================================
tab_mkt, tab_scr, tab_sig, tab_an = st.tabs(L["tabs"])

# ------------------------------------------------------------ MARKET
with tab_mkt:
    st.subheader(L["dca_title"])
    show = ["SPY", "VOO", "QQQ"]
    cols = st.columns(len(show))
    for col, etf in zip(cols, show):
        df = get_history(etf, period)
        if df is None:
            col.warning(f"{etf}: {L['no_data']}")
            continue
        pret = df["Close"].iloc[-1]
        sma200 = df["Close"].rolling(min(200, len(df) - 1)).mean().iloc[-1]
        dist_max = (pret / df["Close"].max() - 1) * 100
        if dist_max <= -10:
            cls, txt = "good", L["dca_good"]
        elif pret < sma200:
            cls, txt = "warn", L["dca_warn"]
        else:
            cls, txt = "", L["dca_norm"]
        with col:
            st.markdown(f'<div class="verdict {cls}"><span class="k">{etf} · '
                        f'{dist_max:+.1f}% {L["vs_max"]}</span>{txt}</div>',
                        unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines",
                                     line=dict(color=BLUE, width=2),
                                     fill="tozeroy", fillcolor="rgba(74,143,224,0.08)"))
            fig.add_trace(go.Scatter(x=df.index,
                                     y=df["Close"].rolling(min(200, len(df) - 1)).mean(),
                                     mode="lines", line=dict(color=GOLD, width=1, dash="dot")))
            fig.update_layout(height=210, margin=dict(l=0, r=0, t=6, b=0), showlegend=False,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              xaxis=dict(showgrid=False, color=MUTED,
                                         tickfont=dict(size=10, family="IBM Plex Mono")),
                              yaxis=dict(gridcolor=LINE, color=MUTED,
                                         range=[df["Close"].min() * 0.97, None],
                                         tickfont=dict(size=10, family="IBM Plex Mono")))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ------------------------------------------------------------ SCREENER
with tab_scr:
    st.subheader(L["scr_title"])
    if st.button(L["scr_run"]):
        rows, bar = [], st.progress(0.0)
        for i, t in enumerate(watchlist):
            info = get_info(t)
            bar.progress((i + 1) / len(watchlist))
            pe, pret = info.get("trailingPE"), info.get("currentPrice")
            if pe is None or pret is None:
                continue
            fpe = info.get("forwardPE")
            peg = info.get("pegRatio")
            pb = info.get("priceToBook")
            div = norm_div(info)
            marja = (info.get("profitMargins") or 0) * 100
            roe = (info.get("returnOnEquity") or 0) * 100
            de = (info.get("debtToEquity") or 0) / 100
            beta = info.get("beta")
            cap = (info.get("marketCap") or 0) / 1e9
            sec = info.get("sector", "—")

            trece = (pe <= max_pe
                     and (fpe is None or fpe <= max_fpe)
                     and (peg is None or peg <= max_peg)
                     and (pb is None or pb <= max_pb)
                     and div >= min_div and marja >= min_marja and roe >= min_roe
                     and de <= max_de
                     and (beta is None or beta <= max_beta)
                     and cap >= min_cap)
            rows.append({C["t"]: t, C["p"]: round(pret, 2), C["pe"]: round(pe, 1),
                         C["fpe"]: round(fpe, 1) if fpe else None,
                         C["peg"]: round(peg, 2) if peg else None,
                         C["pb"]: round(pb, 1) if pb else None,
                         C["div"]: round(div, 1), C["m"]: round(marja, 0),
                         C["roe"]: round(roe, 0), C["de"]: round(de, 2),
                         C["b"]: round(beta, 2) if beta else None,
                         C["cap"]: round(cap, 0), C["sec"]: sec,
                         C["v"]: L["scr_pass"] if trece else "—"})
        bar.empty()
        if rows:
            df_out = pd.DataFrame(rows).sort_values([C["v"], C["pe"]], ascending=[False, True])
            st.dataframe(df_out.style.map(
                lambda v: f"color:{UP};font-weight:600" if v == L["scr_pass"] else f"color:{MUTED}",
                subset=[C["v"]]), use_container_width=True, hide_index=True)
            st.download_button(L["download"], df_out.to_csv(index=False).encode(),
                               "ivy_trading_screener.csv", "text/csv")
            st.caption(L["scr_note"])
        else:
            st.warning(L["scr_empty"])

# ------------------------------------------------------------ SIGNALS
with tab_sig:
    st.subheader(L["sig_title"])
    if st.button(L["sig_run"]):
        semnale, bar = [], st.progress(0.0)
        for i, t in enumerate(watchlist):
            df = get_history(t, "1y")
            bar.progress((i + 1) / len(watchlist))
            if df is None or len(df) < ma_slow + 10:
                continue
            close, vol = df["Close"], df["Volume"]
            pret = close.iloc[-1]
            rsi = calc_rsi(close).iloc[-1]
            f_ma = close.rolling(ma_fast).mean()
            s_ma = close.rolling(ma_slow).mean()

            msgs = []
            if rsi <= rsi_jos:
                msgs.append(f"RSI {rsi:.0f} — {L['oversold']}")
            elif rsi >= rsi_sus:
                msgs.append(f"RSI {rsi:.0f} — {L['overbought']}")
            if f_ma.iloc[-6] < s_ma.iloc[-6] and f_ma.iloc[-1] > s_ma.iloc[-1]:
                msgs.append(f"Golden Cross {ma_fast}/{ma_slow}")
            if f_ma.iloc[-6] > s_ma.iloc[-6] and f_ma.iloc[-1] < s_ma.iloc[-1]:
                msgs.append(f"Death Cross {ma_fast}/{ma_slow}")
            if use_macd:
                macd, sig = calc_macd(close)
                if macd.iloc[-2] < sig.iloc[-2] and macd.iloc[-1] > sig.iloc[-1]:
                    msgs.append(L["macd_up"])
                if macd.iloc[-2] > sig.iloc[-2] and macd.iloc[-1] < sig.iloc[-1]:
                    msgs.append(L["macd_dn"])
            if use_52w:
                if pret <= close.min() * 1.05:
                    msgs.append(L["near_low"])
                if pret >= close.max() * 0.98:
                    msgs.append(L["near_high"])
            if use_vol and vol.iloc[-1] > vol.rolling(50).mean().iloc[-1] * 2:
                msgs.append(L["vol_spike"])

            if msgs:
                semnale.append({C["t"]: t, C["p"]: round(pret, 2),
                                C["sig"]: " · ".join(msgs)})
        bar.empty()
        if semnale:
            st.dataframe(pd.DataFrame(semnale), use_container_width=True, hide_index=True)
        else:
            st.info(L["sig_empty"])
        st.caption(L["sig_note"])

# ------------------------------------------------------------ SINGLE STOCK
with tab_an:
    st.subheader(L["an_title"])
    tk = st.selectbox(L["an_pick"], watchlist)
    if tk:
        df = get_history(tk, period)
        info = get_info(tk)
        if df is None:
            st.warning(L["no_data"])
        else:
            close = df["Close"]
            pret = close.iloc[-1]
            chg = (pret / close.iloc[-2] - 1) * 100 if len(close) > 1 else 0
            rsi_series = calc_rsi(close)

            # Stat cards
            div = norm_div(info)
            cap = (info.get("marketCap") or 0) / 1e9
            lo, hi = close.min(), close.max()
            stats = [
                (L["price"], f"${pret:,.2f}"),
                (L["chg_day"], f"{chg:+.2f}%"),
                (L["pe"], f"{info.get('trailingPE'):.1f}" if info.get("trailingPE") else "—"),
                (L["fpe"], f"{info.get('forwardPE'):.1f}" if info.get("forwardPE") else "—"),
                (L["div"], f"{div:.1f}%"),
                (L["cap"], f"${cap:,.0f}B"),
                (L["beta"], f"{info.get('beta'):.2f}" if info.get("beta") else "—"),
                (L["target"], f"${info.get('targetMeanPrice'):,.0f}" if info.get("targetMeanPrice") else "—"),
            ]
            cols = st.columns(4)
            for i, (k, v) in enumerate(stats):
                cols[i % 4].markdown(
                    f'<div class="stat"><div class="k">{k}</div><div class="v">{v}</div></div>',
                    unsafe_allow_html=True)
            st.markdown(
                f'<div class="stat"><div class="k">{L["range52"]} · {L["sector"]}</div>'
                f'<div class="v">${lo:,.2f} — ${hi:,.2f} · {info.get("sector", "—")}</div></div>',
                unsafe_allow_html=True)

            # Price + RSI chart
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                row_heights=[0.72, 0.28], vertical_spacing=0.06)
            fig.add_trace(go.Scatter(x=df.index, y=close, mode="lines", name=L["price"],
                                     line=dict(color=BLUE, width=2),
                                     fill="tozeroy", fillcolor="rgba(74,143,224,0.07)"), 1, 1)
            fig.add_trace(go.Scatter(x=df.index, y=close.rolling(ma_fast).mean(),
                                     mode="lines", name=f"SMA {ma_fast}",
                                     line=dict(color=GOLD, width=1)), 1, 1)
            fig.add_trace(go.Scatter(x=df.index, y=close.rolling(min(ma_slow, len(df) - 1)).mean(),
                                     mode="lines", name=f"SMA {ma_slow}",
                                     line=dict(color=MUTED, width=1, dash="dot")), 1, 1)
            fig.add_trace(go.Scatter(x=df.index, y=rsi_series, mode="lines", name="RSI",
                                     line=dict(color=GOLD, width=1.5)), 2, 1)
            fig.add_hline(y=rsi_sus, line=dict(color=DOWN, width=1, dash="dot"), row=2, col=1)
            fig.add_hline(y=rsi_jos, line=dict(color=UP, width=1, dash="dot"), row=2, col=1)
            fig.update_layout(height=460, margin=dict(l=0, r=0, t=10, b=0),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              legend=dict(orientation="h", y=1.06,
                                          font=dict(size=10, family="IBM Plex Mono", color=MUTED)))
            fig.update_xaxes(showgrid=False, color=MUTED,
                             tickfont=dict(size=10, family="IBM Plex Mono"))
            fig.update_yaxes(gridcolor=LINE, color=MUTED,
                             tickfont=dict(size=10, family="IBM Plex Mono"))
            fig.update_yaxes(range=[close.min() * 0.95, None], row=1, col=1)
            fig.update_yaxes(range=[0, 100], row=2, col=1)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Current signals
            msgs = []
            rsi_now = rsi_series.iloc[-1]
            if rsi_now <= rsi_jos:
                msgs.append(f"RSI {rsi_now:.0f} — {L['oversold']}")
            elif rsi_now >= rsi_sus:
                msgs.append(f"RSI {rsi_now:.0f} — {L['overbought']}")
            if pret <= lo * 1.05:
                msgs.append(L["near_low"])
            if pret >= hi * 0.98:
                msgs.append(L["near_high"])
            if msgs:
                st.markdown(f'<div class="verdict"><span class="k">{L["signals_now"]}</span>'
                            f'{" · ".join(msgs)}</div>', unsafe_allow_html=True)

# ============================================================
# LEGAL
# ============================================================
st.markdown(f'<div class="legal">{L["legal"]}</div>', unsafe_allow_html=True)
