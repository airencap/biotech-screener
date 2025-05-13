import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import datetime

st.set_page_config(page_title="Biotech Screener", layout="wide")

st.title("🧬 Undervalued US Biotech Screener")
st.markdown("""
This app scans **US-listed biotech companies** and identifies those where:

**Cash per Share ≥ Current Stock Price**

Great for spotting deep value or potential arbitrage in small caps.
""")

# Fetch biotech tickers from Finviz with 24-hour caching
@st.cache_data(ttl=86400, show_spinner=False)
def fetch_biotech_tickers_from_finviz():
    url = "https://finviz.com/screener.ashx?v=111&f=ind_biotechnology&o=-marketcap"
    headers = {'User-Agent': 'Mozilla/5.0'}
    tickers = []
    for page in range(0, 10):  # 10 pages * 20 = 200 stocks
        full_url = f"{url}&r={1 + page * 20}"
        response = requests.get(full_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        for row in soup.select("table.table-dark-row-cp tr[valign='top']"):
            tds = row.find_all("td")
            if tds:
                tickers.append(tds[1].text.strip())
    return tickers

biotech_tickers = fetch_biotech_tickers_from_finviz()

# Cash/share threshold
threshold = st.sidebar.number_input(
    "Cash/Share must be at least this multiple of Price:", min_value=0.0, max_value=5.0, value=1.0, step=0.1
)

@st.cache_data(show_spinner=False)
def fetch_data(tickers, threshold):
    results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            price = info.get("currentPrice")
            shares_outstanding = info.get("sharesOutstanding")
            total_cash = info.get("totalCash")
            name = info.get("shortName", "N/A")
            sector = info.get("sector", "N/A")
            market_cap = info.get("marketCap")

            if all([price, shares_outstanding, total_cash]):
                cash_per_share = total_cash / shares_outstanding
                if cash_per_share >= threshold * price:
                    results.append({
                        "Ticker": ticker,
                        "Company": name,
                        "Sector": sector,
                        "Price": price,
                        "Cash/Share": round(cash_per_share, 2),
                        "Market Cap": market_cap
                    })
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            continue
    return pd.DataFrame(results)

# Auto-run screener
st.subheader("📊 Screening Results")
df = fetch_data(biotech_tickers, threshold)

if not df.empty:
    st.success(f"Found {len(df)} undervalued biotech companies!")
    st.dataframe(df)
    st.download_button("📥 Download CSV", df.to_csv(index=False), "undervalued_biotechs.csv")
else:
    st.warning("No companies met the criteria.")
