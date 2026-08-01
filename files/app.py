"""
ANALIZA BURSA - aplicatie web (Streamlit)
==========================================
Rulare locala:  streamlit run app.py
Deploy gratuit: share.streamlit.io (Streamlit Community Cloud)
"""

from datetime import datetime

import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Analiza Bursa S&P 500", page_icon="📈", layout="wide")

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
# DATE (cu cache ca sa nu abuzam de Yahoo Finance)
# ============================================================

@st.cache_data(ttl=3600, show_spinner=False)
def get_history(ticker: str, period: str = "1y") -> pd.DataFrame | None:
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


# ============================================================
# UI
# ============================================================

st.title("📈 Analiza Bursa — S&P 500")
st.caption(
    f"Actualizat: {datetime.now():%d.%m.%Y %H:%M} · Date: Yahoo Finance (intarziere ~15 min) · "
    "Instrument informativ — NU reprezinta consultanta financiara sau recomandare de investitii."
)

with st.sidebar:
    st.header("⚙️ Setari")
    tickers_input = st.text_area(
        "Watchlist (tickere separate prin virgula)",
        value=", ".join(WATCHLIST_DEFAULT),
        height=120,
    )
    watchlist = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    st.subheader("Filtre screener")
    max_pe = st.slider("P/E maxim", 5, 50, 20)
    max_peg = st.slider("PEG maxim", 0.5, 3.0, 1.5, 0.1)
    min_div = st.slider("Dividend minim (%)", 0.0, 6.0, 0.0, 0.5)
    min_marja = st.slider("Marja profit minima (%)", 0, 40, 10)

    st.subheader("Praguri RSI")
    rsi_jos = st.slider("Supravandut sub", 20, 40, 30)
    rsi_sus = st.slider("Supracumparat peste", 60, 85, 70)

tab_dca, tab_screener, tab_swing = st.tabs(
    ["🏦 Monitor DCA", "💰 Screener valoare", "📊 Semnale tehnice"]
)

# ------------------------------------------------------------
# TAB 1: DCA
# ------------------------------------------------------------
with tab_dca:
    st.subheader("Termen lung — e piata la reducere?")
    cols = st.columns(len(DCA_ETFS))
    for col, etf in zip(cols, DCA_ETFS):
        df = get_history(etf)
        if df is None:
            col.warning(f"{etf}: date indisponibile")
            continue
        pret = df["Close"].iloc[-1]
        sma200 = df["Close"].rolling(200).mean().iloc[-1]
        max52 = df["Close"].max()
        dist_max = (pret / max52 - 1) * 100

        col.metric(etf, f"${pret:,.2f}", f"{dist_max:+.1f}% vs max 52 sapt")
        if dist_max <= -10:
            col.success("Corectie >10% — istoric, moment bun de suplimentat DCA")
        elif pret < sma200:
            col.info("Sub media de 200 zile — pret sub trend")
        else:
            col.write("Trend normal — DCA lunar standard")

        col.line_chart(df["Close"], height=180)

# ------------------------------------------------------------
# TAB 2: SCREENER
# ------------------------------------------------------------
with tab_screener:
    st.subheader("Companii solide la pret rezonabil")
    if st.button("🔍 Ruleaza screener", type="primary"):
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
            trece = (
                pe <= max_pe
                and (peg is None or peg <= max_peg)
                and div >= min_div
                and marja >= min_marja
            )
            rows.append({
                "Ticker": t, "Pret ($)": round(pret, 2), "P/E": round(pe, 1),
                "PEG": round(peg, 2) if peg else None,
                "Dividend (%)": round(div, 1), "Marja (%)": round(marja, 0),
                "Trece filtrele": "✅" if trece else "—",
            })
        bar.empty()
        if rows:
            df_out = pd.DataFrame(rows).sort_values("Trece filtrele", ascending=False)
            st.dataframe(df_out, use_container_width=True, hide_index=True)
            st.caption("Un P/E mic nu inseamna automat 'ieftin' — verifica de ce e mic.")
        else:
            st.warning("Nu s-au putut incarca date pentru watchlist.")

# ------------------------------------------------------------
# TAB 3: SWING
# ------------------------------------------------------------
with tab_swing:
    st.subheader("Semnale tehnice pe watchlist")
    if st.button("📊 Cauta semnale", type="primary"):
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
                msgs.append(f"🟢 RSI {rsi:.0f} — supravandut")
            elif rsi >= rsi_sus:
                msgs.append(f"🔴 RSI {rsi:.0f} — supracumparat")
            if sma50.iloc[-6] < sma200.iloc[-6] and sma50.iloc[-1] > sma200.iloc[-1]:
                msgs.append("⭐ Golden Cross")
            if sma50.iloc[-6] > sma200.iloc[-6] and sma50.iloc[-1] < sma200.iloc[-1]:
                msgs.append("⚠️ Death Cross")
            if pret <= close.min() * 1.05:
                msgs.append("📉 la <5% de minimul pe 52 sapt")

            if msgs:
                semnale.append({"Ticker": t, "Pret ($)": round(pret, 2),
                                "Semnale": " | ".join(msgs)})
        bar.empty()
        if semnale:
            st.dataframe(pd.DataFrame(semnale), use_container_width=True, hide_index=True)
        else:
            st.info("Niciun semnal tehnic notabil azi.")
        st.caption("Semnalele tehnice sunt indicii, nu predictii.")

st.divider()
st.caption(
    "⚠️ Acest site are scop strict informativ si educational. Nu constituie consultanta "
    "financiara, recomandare de investitii sau oferta de servicii de investitii. "
    "Investitiile la bursa implica risc de pierdere a capitalului. Performanta trecuta "
    "nu garanteaza rezultate viitoare."
)
