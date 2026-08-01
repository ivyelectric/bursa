"""
PULS BURSA - terminal de analiza S&P 500
=========================================
Rulare locala:  streamlit run app.py
Deploy gratuit: share.streamlit.io
"""

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Puls Bursa — S&P 500", page_icon="◮", layout="wide")

# ============================================================
# DESIGN — paleta si stiluri
# ============================================================
INK = "#0C1220"        # fundal principal
PANEL = "#141C2E"      # carduri / panouri
LINE = "#243049"       # borduri fine
TEXT = "#E6EAF2"       # text principal
MUTED = "#8A94A8"      # text secundar
GOLD = "#E8B44C"       # accent — ambra de ticker
UP = "#3DD68C"         # crestere
DOWN = "#F26D6D"       # scadere

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

h1, h2, h3 {{ font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.01em; }}

.block-container {{ padding-top: 1.6rem; max-width: 1200px; }}

/* Antet marca */
.brand {{
    display: flex; align-items: baseline; gap: .75rem;
    border-bottom: 1px solid {LINE}; padding-bottom: 1rem; margin-bottom: .25rem;
}}
.brand .logo {{
    font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.9rem;
    color: {TEXT};
}}
.brand .logo span {{ color: {GOLD}; }}
.brand .tag {{
    font-family: 'IBM Plex Mono', monospace; font-size: .72rem; color: {MUTED};
    text-transform: uppercase; letter-spacing: .14em;
}}

/* Banda ticker — semnatura paginii */
.tickerband {{
    display: flex; flex-wrap: wrap; gap: 0;
    background: {PANEL}; border: 1px solid {LINE}; border-radius: 10px;
    margin: 1rem 0 1.4rem 0; overflow: hidden;
}}
.tick {{
    flex: 1 1 140px; padding: .8rem 1.1rem;
    border-right: 1px solid {LINE};
    font-family: 'IBM Plex Mono', monospace;
}}
.tick:last-child {{ border-right: none; }}
.tick .sym {{ font-size: .72rem; color: {MUTED}; letter-spacing: .12em; }}
.tick .px  {{ font-size: 1.25rem; font-weight: 600; color: {TEXT}; margin: .1rem 0; }}
.tick .chg {{ font-size: .8rem; font-weight: 500; }}

/* Carduri verdict */
.verdict {{
    background: {PANEL}; border: 1px solid {LINE}; border-left: 3px solid {GOLD};
    border-radius: 8px; padding: .8rem 1rem; font-size: .88rem; color: {TEXT};
    margin-bottom: .8rem;
}}
.verdict.good {{ border-left-color: {UP}; }}
.verdict.warn {{ border-left-color: {DOWN}; }}
.verdict .k {{
    font-family: 'IBM Plex Mono', monospace; font-size: .7rem; color: {MUTED};
    text-transform: uppercase; letter-spacing: .12em; display:block; margin-bottom:.2rem;
}}

/* Tab-uri */
.stTabs [data-baseweb="tab-list"] {{ gap: .3rem; border-bottom: 1px solid {LINE}; }}
.stTabs [data-baseweb="tab"] {{
    font-family: 'IBM Plex Mono', monospace; font-size: .8rem; letter-spacing: .06em;
    text-transform: uppercase; color: {MUTED}; padding: .55rem 1rem;
    background: transparent; border-radius: 8px 8px 0 0;
}}
.stTabs [aria-selected="true"] {{ color: {GOLD} !important; border-bottom: 2px solid {GOLD}; }}

/* Butoane */
.stButton > button {{
    font-family: 'IBM Plex Mono', monospace; text-transform: uppercase;
    letter-spacing: .08em; font-size: .78rem; font-weight: 600;
    background: {GOLD}; color: {INK}; border: none; border-radius: 8px;
    padding: .55rem 1.3rem;
}}
.stButton > button:hover {{ background: #F2C468; color: {INK}; }}

/* Tabele */
[data-testid="stDataFrame"] {{ border: 1px solid {LINE}; border-radius: 10px; }}

/* Sidebar */
[data-testid="stSidebar"] {{ border-right: 1px solid {LINE}; }}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
    font-family: 'IBM Plex Mono', monospace !important; font-size: .78rem !important;
    text-transform: uppercase; letter-spacing: .12em; color: {MUTED} !important;
}}

/* Nota subsol */
.legal {{
    font-size: .72rem; color: {MUTED}; border-top: 1px solid {LINE};
    padding-top: 1rem; margin-top: 2rem; line-height: 1.5;
}}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONFIG
# ============================================================
WATCHLIST_DEFAULT = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
    "JPM", "V", "MA", "UNH", "JNJ", "PG", "KO", "PEP",
    "XOM", "CVX", "HD", "COST", "WMT", "DIS", "NFLX",
    "AMD", "INTC", "CRM", "ORCL", "ADBE", "CSCO", "PFE", "MRK",
]
DCA_ETFS = ["SPY", "VOO", "QQQ"]

# ============================================================
# DATE (cache 1h)
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

def calc_rsi(prices: pd.Series, period: int = 14) -> float:
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return float((100 - 100 / (1 + rs)).iloc[-1])

def chart_area(df: pd.DataFrame, color: str = GOLD) -> go.Figure:
    """Grafic de pret cu umplere gradient, stil terminal."""
    sma200 = df["Close"].rolling(200).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"], mode="lines", name="Pret",
        line=dict(color=color, width=2),
        fill="tozeroy", fillcolor="rgba(232,180,76,0.08)",
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=sma200, mode="lines", name="SMA 200",
        line=dict(color=MUTED, width=1, dash="dot"),
    ))
    ymin = df["Close"].min() * 0.97
    fig.update_layout(
        height=220, margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(showgrid=False, color=MUTED, tickfont=dict(size=10, family="IBM Plex Mono")),
        yaxis=dict(gridcolor=LINE, color=MUTED, range=[ymin, None],
                   tickfont=dict(size=10, family="IBM Plex Mono")),
    )
    return fig

# ============================================================
# ANTET + BANDA TICKER (semnatura)
# ============================================================
st.markdown(f"""
<div class="brand">
  <div class="logo">PULS<span>◮</span>BURSA</div>
  <div class="tag">Analiza S&amp;P 500 · {datetime.now():%d.%m.%Y}</div>
</div>
""", unsafe_allow_html=True)

etf_data = {etf: get_history(etf) for etf in DCA_ETFS}

ticks_html = ""
for etf, df in etf_data.items():
    if df is None or len(df) < 2:
        continue
    pret = df["Close"].iloc[-1]
    prev = df["Close"].iloc[-2]
    chg = (pret / prev - 1) * 100
    culoare = UP if chg >= 0 else DOWN
    sageata = "▲" if chg >= 0 else "▼"
    ticks_html += (
        f'<div class="tick"><div class="sym">{etf}</div>'
        f'<div class="px">${pret:,.2f}</div>'
        f'<div class="chg" style="color:{culoare}">{sageata} {chg:+.2f}%</div></div>'
    )
st.markdown(f'<div class="tickerband">{ticks_html}</div>', unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("Watchlist")
    tickers_input = st.text_area(
        "Tickere (separate prin virgula)",
        value=", ".join(WATCHLIST_DEFAULT), height=120, label_visibility="collapsed",
    )
    watchlist = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    st.header("Filtre screener")
    max_pe = st.slider("P/E maxim", 5, 50, 20)
    max_peg = st.slider("PEG maxim", 0.5, 3.0, 1.5, 0.1)
    min_div = st.slider("Dividend minim (%)", 0.0, 6.0, 0.0, 0.5)
    min_marja = st.slider("Marja profit minima (%)", 0, 40, 10)

    st.header("Praguri RSI")
    rsi_jos = st.slider("Supravandut sub", 20, 40, 30)
    rsi_sus = st.slider("Supracumparat peste", 60, 85, 70)

# ============================================================
# TAB-URI
# ============================================================
tab_dca, tab_screener, tab_swing = st.tabs(["Monitor DCA", "Screener valoare", "Semnale tehnice"])

# ------------------------------------------------------------
with tab_dca:
    st.subheader("Termen lung — e piata la reducere?")
    cols = st.columns(len(DCA_ETFS))
    for col, etf in zip(cols, DCA_ETFS):
        df = etf_data.get(etf)
        if df is None:
            col.warning(f"{etf}: date indisponibile")
            continue
        pret = df["Close"].iloc[-1]
        sma200 = df["Close"].rolling(200).mean().iloc[-1]
        dist_max = (pret / df["Close"].max() - 1) * 100

        if dist_max <= -10:
            cls, txt = "good", "Corectie de peste 10% fata de maxim — istoric, moment favorabil de suplimentat DCA."
        elif pret < sma200:
            cls, txt = "warn", "Sub media de 200 zile — pret sub trend, de urmarit."
        else:
            cls, txt = "", "Trend normal — continua DCA lunar standard."

        with col:
            st.markdown(
                f'<div class="verdict {cls}"><span class="k">{etf} · '
                f'{dist_max:+.1f}% vs max 52 sapt</span>{txt}</div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(chart_area(df), use_container_width=True,
                            config={"displayModeBar": False})

# ------------------------------------------------------------
with tab_screener:
    st.subheader("Companii solide la pret rezonabil")
    if st.button("Ruleaza screener"):
        rows = []
        bar = st.progress(0.0)
        for i, t in enumerate(watchlist):
            info = get_info(t)
            bar.progress((i + 1) / len(watchlist))
            pe = info.get("trailingPE")
            pret = info.get("currentPrice")
            if pe is None or pret is None:
                continue
            peg = info.get("pegRatio")
            div = (info.get("dividendYield") or 0)
            div = div * 100 if div < 1 else div
            marja = (info.get("profitMargins") or 0) * 100
            trece = (pe <= max_pe and (peg is None or peg <= max_peg)
                     and div >= min_div and marja >= min_marja)
            rows.append({
                "Ticker": t, "Pret ($)": round(pret, 2), "P/E": round(pe, 1),
                "PEG": round(peg, 2) if peg else None,
                "Dividend (%)": round(div, 1), "Marja (%)": round(marja, 0),
                "Verdict": "TRECE" if trece else "—",
            })
        bar.empty()
        if rows:
            df_out = pd.DataFrame(rows).sort_values(["Verdict", "P/E"], ascending=[False, True])
            st.dataframe(
                df_out.style.map(
                    lambda v: f"color:{UP};font-weight:600" if v == "TRECE" else f"color:{MUTED}",
                    subset=["Verdict"],
                ),
                use_container_width=True, hide_index=True,
            )
            st.caption("Un P/E mic nu inseamna automat 'ieftin' — verifica de ce e mic.")
        else:
            st.warning("Nu s-au putut incarca date pentru watchlist.")

# ------------------------------------------------------------
with tab_swing:
    st.subheader("Semnale tehnice pe watchlist")
    if st.button("Cauta semnale"):
        semnale = []
        bar = st.progress(0.0)
        for i, t in enumerate(watchlist):
            df = get_history(t)
            bar.progress((i + 1) / len(watchlist))
            if df is None or len(df) < 200:
                continue
            close = df["Close"]
            pret = close.iloc[-1]
            rsi = calc_rsi(close)
            sma50 = close.rolling(50).mean()
            sma200 = close.rolling(200).mean()

            msgs = []
            if rsi <= rsi_jos:
                msgs.append(f"RSI {rsi:.0f} — supravandut")
            elif rsi >= rsi_sus:
                msgs.append(f"RSI {rsi:.0f} — supracumparat")
            if sma50.iloc[-6] < sma200.iloc[-6] and sma50.iloc[-1] > sma200.iloc[-1]:
                msgs.append("Golden Cross")
            if sma50.iloc[-6] > sma200.iloc[-6] and sma50.iloc[-1] < sma200.iloc[-1]:
                msgs.append("Death Cross")
            if pret <= close.min() * 1.05:
                msgs.append("la <5% de minimul pe 52 sapt")

            if msgs:
                semnale.append({"Ticker": t, "Pret ($)": round(pret, 2),
                                "Semnale": " · ".join(msgs)})
        bar.empty()
        if semnale:
            st.dataframe(pd.DataFrame(semnale), use_container_width=True, hide_index=True)
        else:
            st.info("Niciun semnal tehnic notabil azi.")
        st.caption("Semnalele tehnice sunt indicii, nu predictii.")

# ============================================================
# SUBSOL LEGAL
# ============================================================
st.markdown(f"""
<div class="legal">
Date: Yahoo Finance, cu intarziere de aproximativ 15 minute si cache de 1 ora.
Acest site are scop strict informativ si educational. Nu constituie consultanta financiara,
recomandare de investitii sau oferta de servicii de investitii. Investitiile la bursa implica
risc de pierdere a capitalului. Performanta trecuta nu garanteaza rezultate viitoare.
</div>
""", unsafe_allow_html=True)
