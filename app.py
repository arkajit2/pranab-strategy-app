import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# ------------------ PAGE SETUP ------------------ #
st.set_page_config(page_title="Pranab Strategy 4 - Intraday", layout="wide")
st_autorefresh(interval=300000, key="fivedata")

st.title("🕒 Pranab Strategy 4 - Intraday Scanner")
st.info("EMA + RSI + Volume Strategy (Final Logic)")

# ------------------ STOCK LIST ------------------ #
TICKERS = [
    "AARTIIND.NS", "ABB.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS",
    "ACC.NS", "ADANIGREEN.NS", "ADANIPORTS.NS", "ADANIENSOL.NS", "ADANIENT.NS"
]

# ------------------ INDICATORS ------------------ #
def add_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['EMA100'] = df['Close'].ewm(span=100).mean()
    df['EMA200'] = df['Close'].ewm(span=200).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    df['RSI14'] = 100 - (100 / (1 + rs))

    return df

# ------------------ DATA FETCH ------------------ #
@st.cache_data(ttl=300)
def fetch_data(tickers):

    try:
        df = yf.download(
            tickers=tickers,
            period="10d",
            interval="5m",
            group_by="ticker",
            progress=False,
            threads=False
        )
    except Exception:
        return pd.DataFrame()

    results = []

    for ticker in tickers:
        try:
            stock_df = df[ticker].dropna()

            if stock_df.empty:
                continue

            stock_df = add_indicators(stock_df)

            latest = stock_df.iloc[-1]
            prev = stock_df.iloc[-2] if len(stock_df) > 1 else latest

            # ------------------ BUY LOGIC ------------------ #
            buy = (
                latest['Close'] > latest['EMA20'] and
                latest['EMA20'] > latest['EMA50'] > latest['EMA100'] > latest['EMA200'] and
                latest['RSI14'] > 50 and
                latest['Volume'] > prev['Volume'] and
                latest['Volume'] > 500000
            )

            # ------------------ SELL LOGIC (UPDATED) ------------------ #
            sell = (
                latest['Close'] < latest['EMA200'] and
                latest['EMA20'] < latest['EMA50'] < latest['EMA100'] < latest['EMA200'] and
                latest['RSI14'] < 50 and
                latest['Volume'] < prev['Volume'] and
                latest['Volume'] > 500000
            )

            status = "NEUTRAL"
            if buy:
                status = "🟢 BUY"
            elif sell:
                status = "🔴 SELL"

            results.append({
                "Stock": ticker,
                "Close": round(float(latest['Close']), 2),
                "EMA20": round(float(latest['EMA20']), 2),
                "EMA50": round(float(latest['EMA50']), 2),
                "EMA100": round(float(latest['EMA100']), 2),
                "EMA200": round(float(latest['EMA200']), 2),
                "RSI": round(float(latest['RSI14']), 2),
                "Volume": int(latest['Volume']),
                "Prev Volume": int(prev['Volume']),
                "Status": status
            })

        except Exception:
            continue

    return pd.DataFrame(results)

# ------------------ FETCH ------------------ #
with st.spinner("Fetching market data..."):
    data = fetch_data(TICKERS)

# ------------------ MARKET STATUS ------------------ #
hour = datetime.now().hour
minute = datetime.now().minute

if hour < 9 or (hour == 9 and minute < 15) or hour > 15:
    st.info("ℹ️ Market closed — showing last available data")

# ------------------ METRICS ------------------ #
col1, col2, col3 = st.columns(3)

col1.metric("Time", datetime.now().strftime('%H:%M:%S'))
col2.metric("Stocks", len(TICKERS))

if not data.empty:
    active = len(data[data["Status"] != "NEUTRAL"])
else:
    active = 0

col3.metric("Signals", active)

# ------------------ DISPLAY ------------------ #
tab1, tab2 = st.tabs(["🚀 Signals", "📊 Watchlist"])

with tab1:
    if not data.empty:
        signals = data[data["Status"] != "NEUTRAL"]

        if not signals.empty:
            st.dataframe(signals, use_container_width=True)
        else:
            st.write("No active signals")
    else:
        st.warning("No data returned")

with tab2:
    if not data.empty:
        st.dataframe(data, use_container_width=True)

# ------------------ REFRESH ------------------ #
if st.button("🔄 Refresh"):
    st.cache_data.clear()

st.caption("Auto-refresh every 5 minutes")
