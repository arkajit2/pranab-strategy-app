import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# ------------------ PAGE SETUP ------------------ #
st.set_page_config(page_title="Pranab Strategy - Full Market Scanner", layout="wide")
st_autorefresh(interval=300000, key="refresh")

st.title("📊 Pranab Strategy - Full Market Scanner")
st.info("EMA + RSI + Volume Strategy")

# ------------------ STOCK LIST ------------------ #
TICKERS = [
"AARTIIND.NS","ABB.NS","ABBOTINDIA.NS","ABCAPITAL.NS","ABFRL.NS","ACC.NS",
"ADANIENSOL.NS","ADANIENT.NS","ADANIGREEN.NS","ADANIPORTS.NS","ADANIPOWER.NS",
"ALKEM.NS","AMBUJACEM.NS","ANGELONE.NS","APLAPOLLO.NS","APOLLOHOSP.NS",
"APOLLOTYRE.NS","ASHOKLEY.NS","ASIANPAINT.NS","ASTRAL.NS","ATUL.NS",
"AUBANK.NS","AUROPHARMA.NS","AXISBANK.NS","BAJAJ-AUTO.NS","BAJAJFINSV.NS",
"BAJAJHLDNG.NS","BAJFINANCE.NS","BALKRISIND.NS","BANDHANBNK.NS","BANKBARODA.NS",
"BANKINDIA.NS","BEL.NS","BHARATFORG.NS","BHARTIARTL.NS","BHEL.NS","BIOCON.NS",
"BOSCHLTD.NS","BPCL.NS","BRITANNIA.NS","BSE.NS","CANBK.NS","CANFINHOME.NS",
"CDSL.NS","CESC.NS","CGPOWER.NS","CHOLAFIN.NS","CIPLA.NS","COALINDIA.NS",
"COCHINSHIP.NS","COFORGE.NS","COLPAL.NS","CONCOR.NS","COROMANDEL.NS",
"CROMPTON.NS","CUMMINSIND.NS","CYIENT.NS","DABUR.NS","DALBHARAT.NS",
"DEEPAKNTR.NS","DIVISLAB.NS","DIXON.NS","DLF.NS","DRREDDY.NS","EICHERMOT.NS",
"ESCORTS.NS","EXIDEIND.NS","FEDERALBNK.NS","GAIL.NS","GLENMARK.NS",
"GMRAIRPORT.NS","GNFC.NS","GODREJCP.NS","GODREJPROP.NS","GRANULES.NS",
"GRASIM.NS","GUJGASLTD.NS","HAL.NS","HAVELLS.NS","HCLTECH.NS","HDFCAMC.NS",
"HDFCBANK.NS","HDFCLIFE.NS","HEROMOTOCO.NS","HINDALCO.NS","HINDCOPPER.NS",
"HINDPETRO.NS","HINDUNILVR.NS","ICICIBANK.NS","ICICIGI.NS","ICICIPRULI.NS",
"IDFCFIRSTB.NS","IEX.NS","INDHOTEL.NS","INDIANB.NS","INDIGO.NS","INDUSINDBK.NS",
"INFY.NS","IOC.NS","IRCTC.NS","IRFC.NS","ITC.NS","JINDALSTEL.NS","JIOFIN.NS",
"JKCEMENT.NS","JSWENERGY.NS","JSWSTEEL.NS","JUBLFOOD.NS","KOTAKBANK.NS",
"LT.NS","LTTS.NS","LUPIN.NS","M&M.NS","M&MFIN.NS","MANAPPURAM.NS","MARICO.NS",
"MARUTI.NS","MCX.NS","METROPOLIS.NS","MOTHERSON.NS","MOTILALOFS.NS",
"MPHASIS.NS","MRF.NS","MUTHOOTFIN.NS","NAM-INDIA.NS","NATIONALUM.NS",
"NAUKRI.NS","NAVINFLUOR.NS","NESTLEIND.NS","NMDC.NS","NTPC.NS","OBEROIRLTY.NS",
"OFSS.NS","ONGC.NS","PAGEIND.NS","PERSISTENT.NS","PETRONET.NS","PFC.NS",
"PIDILITIND.NS","PIIND.NS","PNB.NS","POLYCAB.NS","PVRINOX.NS","RAMCOCEM.NS",
"RBLBANK.NS","RECLTD.NS","RELIANCE.NS","SAIL.NS","SBICARD.NS","SBILIFE.NS",
"SBIN.NS","SHREECEM.NS","SHRIRAMFIN.NS","SIEMENS.NS","SRF.NS","SUNPHARMA.NS",
"SUNTV.NS","SYNGENE.NS","TATACOMM.NS","TATACONSUM.NS","TATAELXSI.NS",
"TATAPOWER.NS","TATASTEEL.NS","TCS.NS","TECHM.NS","TITAN.NS","TORNTPHARM.NS",
"TRENT.NS","TVSMOTOR.NS","UBL.NS","ULTRACEMCO.NS","UPL.NS","VEDL.NS",
"VGUARD.NS","VOLTAS.NS","WIPRO.NS","YESBANK.NS","ZEEL.NS"
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

# ------------------ FETCH DATA ------------------ #
@st.cache_data(ttl=300)
def fetch_data(tickers):

    df = yf.download(
        tickers=tickers,
        period="10d",
        interval="5m",
        group_by="ticker",
        progress=False,
        threads=False
    )

    results = []

    for ticker in tickers:
        try:
            stock_df = df[ticker].dropna()
            if stock_df.empty:
                continue

            stock_df = add_indicators(stock_df)

            latest = stock_df.iloc[-1]
            prev = stock_df.iloc[-2]

            buy = (
                latest['Close'] > latest['EMA20'] and
                latest['EMA20'] > latest['EMA50'] > latest['EMA100'] > latest['EMA200'] and
                latest['RSI14'] > 50 and
                latest['Volume'] > prev['Volume'] and
                latest['Volume'] > 500000
            )

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
                "Close": round(latest['Close'], 2),
                "EMA20": round(latest['EMA20'], 2),
                "EMA50": round(latest['EMA50'], 2),
                "EMA100": round(latest['EMA100'], 2),
                "EMA200": round(latest['EMA200'], 2),
                "RSI": round(latest['RSI14'], 2),
                "Volume": int(latest['Volume']),
                "Prev Volume": int(prev['Volume']),
                "Status": status
            })

        except:
            continue

    return pd.DataFrame(results)

# ------------------ RUN ------------------ #
data = fetch_data(TICKERS)

st.subheader("📊 Results")

if not data.empty:
    st.dataframe(data, use_container_width=True)
else:
    st.error("No data fetched")
