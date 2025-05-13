import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Biotech Screener", layout="wide")

st.title("🧬 Biotech Screener — Debug Mode")
st.markdown("This version limits ticker count and disables clinical trials/charts by default.")

# Limit Finviz scrape to 2 pages (40 stocks)
@st.cache_data(ttl=86400, show_spinner=False)
def fetch_biotech_tickers():
    url = "https://finviz.com/screener.ashx?v=111&f=ind_biotechnology&o=-marketcap"
    headers = {'User-Agent': 'Mozilla/5.0'}
    tickers = []
    for page in range(0, 2):
        full_url = f"{url}&r={1 + page * 20}"
        response = requests.get(full_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        for row in soup.select("table.table-dark-row-cp tr[valign='top']"):
            tds = row.find_all("td")
            if tds:
                tickers.append(tds[1].text.strip())
    return tickers

tickers = fetch_biotech_tickers()

# Sidebar filters
threshold = st.sidebar.number_input("Cash/Share ≥ Price (multiple)", 0.0, 5.0, 1.0, 0.1)
apply_market_cap = st.sidebar.checkbox("Filter by Market Cap", True)
min_cap = st.sidebar.number_input("Min Market Cap ($B)", 0.0, 500.0, 0.0, 0.1) * 1e9
max_cap = st.sidebar.number_input("Max Market Cap ($B)", 0.1, 500.0, 10.0, 0.1) * 1e9
apply_de_ratio = st.sidebar.checkbox("Max Debt/Equity Ratio", False)
max_de_ratio = st.sidebar.number_input("Max D/E Ratio", 0.0, 10.0, 1.0, 0.1)

@st.cache_data(show_spinner=True)
def screen_stocks(tickers):
    results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            price = info.get("currentPrice")
            cash = info.get("totalCash")
            shares = info.get("sharesOutstanding")
            mc = info.get("marketCap")
            de = info.get("debtToEquity")
            name = info.get("shortName", ticker)

            if all([price, cash, shares, mc]):
                cps = cash / shares
                if cps >= price * threshold:
                    if apply_market_cap and (mc < min_cap or mc > max_cap): continue
                    if apply_de_ratio and de is not None and de > max_de_ratio: continue
                    results.append({
                        "Ticker": ticker, "Company": name, "Price": price,
                        "Cash/Share": round(cps, 2), "Market Cap": mc, "Debt/Equity": de
                    })
        except:
            continue
    return pd.DataFrame(results)

with st.spinner("Running screener..."):
    df = screen_stocks(tickers)

if not df.empty:
    st.success(f"{len(df)} companies matched.")
    st.dataframe(df)
    st.download_button("📥 Download CSV", df.to_csv(index=False), "results.csv")
else:
    st.warning("No matches found.")
