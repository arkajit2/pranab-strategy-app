import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# 1. Setup Page & Auto-Refresh (Set to 300,000ms = 5 minutes)
st.set_page_config(page_title="Pranab Strategy 4 - 5m Intraday", layout="wide")
st_autorefresh(interval=300000, key="fivedata")

st.title("🕒 Pranab Strategy 4 - 5 Min Intraday")
st.info("The logic is now calculating EMA 20, 50, 100, and 200 based on 5-minute candles.")

# Define your tickers (NSE format for Indian markets)
TICKERS = [
    "AARTIIND.NS", "ABB.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", 
    "ACC.NS", "ADANIGREEN.NS", "ADANIPORTS.NS", "ADANIENSOL.NS", "ADANIENT.NS"
]

@st.cache_data(ttl=290) # Cache for slightly less than refresh window
def fetch_5m_data(ticker_list):
    results = []
    for ticker in ticker_list:
        try:
            # We fetch 7 days of 5m data to ensure EMA 200 is stable
            df = yf.download(ticker, period="7d", interval="5m", progress=False)
            if df.empty or len(df) < 200: continue
            
            # Replicating logic from Pranab Strategy 4 latest excel.xlsx
            df['EMA20'] = ta.ema(df['Close'], length=20)
            df['EMA50'] = ta.ema(df['Close'], length=50)
            df['EMA100'] = ta.ema(df['Close'], length=100)
            df['EMA200'] = ta.ema(df['Close'], length=200)
            df['RSI14'] = ta.rsi(df['Close'], length=14)
            
            # Get latest 5m candle and the one before it
            latest = df.iloc[-1]
            prev_candle = df.iloc[-2]
            
            # --- BUY LOGIC (All 4 EMAs in order + Volume spike) ---
            # Perfect Order: 20 > 50 > 100 > 200
            ema_ordered = (latest['EMA20'] > latest['EMA50'] > 
                           latest['EMA100'] > latest['EMA200'])
            
            # Volume: Current 5m candle > Previous 5m candle
            vol_spike = latest['Volume'] > prev_candle['Volume']
            
            status = "NEUTRAL"
            if ema_ordered and vol_spike:
                status = "🟢 SATISFIED: All 4 (Buy)"
            
            # --- SELL LOGIC (EMA Breakdown) ---
            # Based on the file: EMA 200 > 100 > 50
            elif (latest['EMA200'] > latest['EMA100'] > latest['EMA50']):
                status = "🔴 SELL: EMA 200, 100, 50"
            
            results.append({
                "Stock": ticker,
                "LTP": round(float(latest['Close']), 2),
                "EMA 20": round(float(latest['EMA20']), 2),
                "EMA 50": round(float(latest['EMA50']), 2),
                "EMA 100": round(float(latest['EMA100']), 2),
                "EMA 200": round(float(latest['EMA200']), 2),
                "RSI 14": round(float(latest['RSI14']), 2),
                "Current Vol": int(latest['Volume']),
                "Prev Vol": int(prev_candle['Volume']),
                "Status": status
            })
        except Exception:
            continue
    return pd.DataFrame(results)

# Run logic
data = fetch_5m_data(TICKERS)

# Dashboard Layout
col1, col2, col3 = st.columns(3)
col1.metric("Market Time", datetime.now().strftime('%H:%M:%S'))
col2.metric("Stocks Scanned", len(TICKERS))
col3.metric("Active Signals", len(data[data['Status'] != "NEUTRAL"]))

# Detailed Views
tab1, tab2 = st.tabs(["🚀 Active Signals", "📊 Full Watchlist"])

with tab1:
    signals = data[data['Status'] != "NEUTRAL"]
    if not signals.empty:
        st.dataframe(signals.style.applymap(
            lambda x: 'background-color: #004d00' if 'Buy' in str(x) else ('background-color: #4d0000' if 'Sell' in str(x) else ''),
            subset=['Status']
        ), use_container_width=True)
    else:
        st.write("Monitoring market for 5m EMA setups...")

with tab2:
    st.dataframe(data, use_container_width=True)

st.caption(f"Next refresh at: {(datetime.now().minute // 5 + 1) * 5}:00")
