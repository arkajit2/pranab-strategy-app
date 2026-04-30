import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# Page config
st.set_page_config(page_title="Pranab Strategy 4 - 5m Intraday", layout="wide")

# Auto refresh every 5 minutes
st_autorefresh(interval=300000, key="fivedata")

st.title("🕒 Pranab Strategy 4 - 5 Min Intraday")
st.info("EMA 20, 50, 100, 200 + RSI (No pandas-ta, fully stable)")

# NSE Stocks
TICKERS = [
    "AARTIIND.NS", "ABB.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS",
    "ACC.NS", "ADANIGREEN.NS", "ADANIPORTS.NS", "ADANIENSOL.NS", "ADANIENT.NS"
]

# ---- INDICATOR FUNCTIONS ---- #

def calculate_ema(df):
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA100'] = df['Close'].ewm(span=100, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    return df

def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    df['RSI14'] = 100 - (100 / (1 + rs))
    return df

# ---- DATA FETCH ---- #

@st.cache_data(ttl=290)
def fetch_5m_data(ticker_list):
    results = []

    for ticker in ticker_list:
        try:
            df = yf.download(
                ticker,
                period="7d",
                interval="5m",
                progress=False,
                threads=False
            )

            if df.empty or len(df) < 200:
                continue

            # Indicators
            df = calculate_ema(df)
            df = calculate_rsi(df)

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            # ---- BUY LOGIC ----
            ema_ordered = (
                latest['EMA20'] > latest['EMA50'] >
                latest['EMA100'] > latest['EMA200']
            )

            vol_spike = latest['Volume'] > prev['Volume']

            status = "NEUTRAL"

            if ema_ordered and vol_spike:
                status = "🟢 BUY"
            elif (latest['EMA200'] > latest['EMA100'] > latest['EMA50']):
                status = "🔴 SELL"

            results.append({
                "Stock": ticker,
                "LTP": round(float(latest['Close']), 2),
                "EMA 20": round(float(latest['EMA20']), 2),
                "EMA 50": round(float(latest['EMA50']), 2),
                "EMA 100": round(float(latest['EMA100']), 2),
                "EMA 200": round(float(latest['EMA200']), 2),
                "RSI 14": round(float(latest['RSI14']), 2),
                "Current Vol": int(latest['Volume']),
                "Prev Vol": int(prev['Volume']),
                "Status": status
            })

        except Exception:
            continue

    return pd.DataFrame(results)

# ---- UI ---- #

with st.spinner("Fetching market data..."):
    data = fetch_5m_data(TICKERS)

# Metrics
col1, col2, col3 = st.columns(3)

col1.metric("Market Time", datetime.now().strftime('%H:%M:%S'))
col2.metric("Stocks Scanned", len(TICKERS))
col3.metric("Active Signals", len(data[data['Status'] != "NEUTRAL"]))

# Tabs
tab1, tab2 = st.tabs(["🚀 Active Signals", "📊 Full Watchlist"])

with tab1:
    signals = data[data['Status'] != "NEUTRAL"]

    if not signals.empty:
        st.dataframe(
            signals.style.applymap(
                lambda x: 'background-color: #004d00' if 'BUY' in str(x)
                else ('background-color: #4d0000' if 'SELL' in str(x) else ''),
                subset=['Status']
            ),
            use_container_width=True
        )
    else:
        st.write("Monitoring market for setups...")

with tab2:
    if not data.empty:
        st.dataframe(data, use_container_width=True)
    else:
        st.warning("No data available. Market may be closed.")

# Manual refresh
if st.button("🔄 Refresh Now"):
    st.cache_data.clear()

st.caption(f"Next refresh at: {(datetime.now().minute // 5 + 1) * 5}:00")
