"""
IVY TRADING — Alerte zilnice pe Telegram
=========================================
Ruleaza automat prin GitHub Actions (vezi .github/workflows/alerte.yml)
sau manual:  python alerte_telegram.py

Necesita variabile de mediu:
  TELEGRAM_TOKEN    - token de la @BotFather
  TELEGRAM_CHAT_ID  - chat id de la @userinfobot
"""

import os
from datetime import datetime

import pandas as pd
import requests
import yfinance as yf

# ---- CONFIG ------------------------------------------------
WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO",
    "JPM", "V", "MA", "UNH", "JNJ", "LLY", "PG", "KO", "PEP",
    "XOM", "CVX", "HD", "COST", "WMT", "MCD", "NFLX",
    "AMD", "INTC", "CRM", "ORCL", "ADBE", "QCOM",
]
DCA_ETFS = ["SPY", "QQQ"]
RSI_JOS, RSI_SUS = 30, 70
MA_FAST, MA_SLOW = 50, 200

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


# ---- INDICATORI --------------------------------------------
def rsi(prices: pd.Series, period: int = 14) -> float:
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    return float((100 - 100 / (1 + gain / loss)).iloc[-1])


def macd_cross(close: pd.Series) -> str | None:
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    m = ema12 - ema26
    s = m.ewm(span=9, adjust=False).mean()
    if m.iloc[-2] < s.iloc[-2] and m.iloc[-1] > s.iloc[-1]:
        return "MACD incrucisare in sus"
    if m.iloc[-2] > s.iloc[-2] and m.iloc[-1] < s.iloc[-1]:
        return "MACD incrucisare in jos"
    return None


# ---- SCOR IVY (versiune simplificata pentru alerte) --------
def _ramp(x, lo, hi, invert=False):
    if x is None:
        return None
    v = max(0.0, min(100.0, (x - lo) / (hi - lo) * 100))
    return 100 - v if invert else v


def _avg(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else 50.0


def scor_ivy(info: dict, close: pd.Series, vix: float | None) -> float:
    val = _avg([
        _ramp(info.get("trailingPE"), 10, 40, True),
        _ramp(info.get("pegRatio"), 1.0, 3.0, True),
        _ramp(info.get("priceToBook"), 2, 10, True),
    ])
    qual = _avg([
        _ramp((info.get("returnOnEquity") or 0) * 100, 5, 25),
        _ramp((info.get("profitMargins") or 0) * 100, 5, 30),
        _ramp((info.get("debtToEquity") or 0) / 100, 0.5, 3.0, True),
    ])
    sma200 = close.rolling(200).mean().iloc[-1]
    r = rsi(close)
    mom = _avg([
        _ramp((close.iloc[-1] / sma200 - 1) * 100, -10, 10),
        100 - min(100, abs(r - 55) * 2.5),
        _ramp((close.iloc[-1] / close.max() - 1) * 100, -30, 0),
    ])
    if vix is None:
        mac = 50.0
    else:
        mac = 100.0 if vix <= 15 else (0.0 if vix >= 35 else _ramp(vix, 15, 35, True))
    return (val * 30 + qual * 25 + mom * 30 + mac * 15) / 100


# ---- SCANARE -----------------------------------------------
def scaneaza() -> str:
    linii = [f"IVY TRADING — raport {datetime.now():%d.%m.%Y}", ""]

    # VIX + poarta de piata
    vix = None
    try:
        vdf = yf.Ticker("^VIX").history(period="1mo")
        if not vdf.empty:
            vix = vdf["Close"].iloc[-1]
    except Exception:
        pass
    if vix is not None:
        stare = ("calm" if vix < 15 else ("normal" if vix < 25 else "STRES — prudenta"))
        linii.append(f"VIX: {vix:.1f} ({stare})")
        if vix > 28:
            linii.append(">>> POARTA DE RISC: VIX peste 28 — zi nefavorabila pentru intrari noi.")
        linii.append("")

    # Piata (DCA)
    linii.append("PIATA:")
    for etf in DCA_ETFS:
        try:
            df = yf.Ticker(etf).history(period="1y")
        except Exception:
            continue
        if df.empty:
            continue
        pret = df["Close"].iloc[-1]
        dist = (pret / df["Close"].max() - 1) * 100
        marcaj = " <<< corectie, DCA favorabil" if dist <= -10 else ""
        linii.append(f"  {etf}: ${pret:,.2f} ({dist:+.1f}% vs max 52s){marcaj}")
    linii.append("")

    # Semnale pe watchlist, cu Scor Ivy si avertisment earnings
    semnale = []
    for t in WATCHLIST:
        try:
            tk = yf.Ticker(t)
            df = tk.history(period="1y")
        except Exception:
            continue
        if df.empty or len(df) < MA_SLOW + 10:
            continue
        close = df["Close"]
        pret = close.iloc[-1]
        msgs = []

        r = rsi(close)
        if r <= RSI_JOS:
            msgs.append(f"RSI {r:.0f} supravandut")
        elif r >= RSI_SUS:
            msgs.append(f"RSI {r:.0f} supracumparat")

        f = close.rolling(MA_FAST).mean()
        s = close.rolling(MA_SLOW).mean()
        if f.iloc[-2] < s.iloc[-2] and f.iloc[-1] > s.iloc[-1]:
            msgs.append(f"Golden Cross {MA_FAST}/{MA_SLOW}")
        if f.iloc[-2] > s.iloc[-2] and f.iloc[-1] < s.iloc[-1]:
            msgs.append(f"Death Cross {MA_FAST}/{MA_SLOW}")

        mc = macd_cross(close)
        if mc:
            msgs.append(mc)

        if pret <= close.min() * 1.05:
            msgs.append("aproape de minim 52s")

        if msgs:
            # doar pentru cele cu semnale calculam scorul (economie de apeluri)
            try:
                info = tk.info
            except Exception:
                info = {}
            scor = scor_ivy(info, close, vix)

            # poarta de risc: earnings in urmatoarele 7 zile?
            gate = ""
            try:
                ed = tk.get_earnings_dates(limit=4)
                if ed is not None and not ed.empty:
                    now = pd.Timestamp.now(tz=ed.index.tz)
                    viitoare = ed.index[ed.index >= now]
                    if len(viitoare):
                        zile = (viitoare.min().tz_localize(None) - pd.Timestamp.now()).days
                        if 0 <= zile <= 7:
                            gate = f" | BLOCAT: earnings in {zile} zile"
            except Exception:
                pass
            if scor < 40 and not gate:
                gate = f" | BLOCAT: scor sub 40"

            semnale.append(f"  {t} (${pret:,.2f}) Scor {scor:.0f}: "
                           + " | ".join(msgs) + gate)

    if semnale:
        linii.append("SEMNALE (cu Scor Ivy):")
        linii.extend(semnale)
    else:
        linii.append("SEMNALE: niciunul notabil azi.")

    linii += ["", "Instrument informativ, nu consultanta financiara."]
    return "\n".join(linii)


# ---- TRIMITERE ---------------------------------------------
def trimite(text: str):
    if not TOKEN or not CHAT_ID:
        print("Lipsesc TELEGRAM_TOKEN / TELEGRAM_CHAT_ID — afisez doar in consola.\n")
        print(text)
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    for i in range(0, len(text), 4000):
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": text[i:i + 4000]}, timeout=20)
        r.raise_for_status()
    print("Trimis pe Telegram.")


if __name__ == "__main__":
    trimite(scaneaza())
