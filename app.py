import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="Biotech Screener", layout="wide")

# CSS for dark mode toggle
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

if st.sidebar.checkbox("🌙 Dark Mode", value=st.session_state.dark_mode):
    st.session_state.dark_mode = True
    st.markdown("""
        <style>
            body, .reportview-container, .main { background-color: #111 !important; color: #eee !important; }
            .stButton>button { background-color: #333; color: white; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.session_state.dark_mode = False

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
    for page in range(0, 10):
        full_url = f"{url}&r={1 + page * 20}"
        response = requests.get(full_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        for row in soup.select("table.table-dark-row-cp tr[valign='top']"):
            tds = row.find_all("td")
            if tds:
                tickers.append(tds[1].text.strip())
    return tickers

biotech_tickers = fetch_biotech_tickers_from_finviz()

# Sidebar filters
st.sidebar.header("🔎 Filters")
threshold = st.sidebar.number_input("Cash/Share must be ≥ x * Price:", min_value=0.0, max_value=5.0, value=1.0, step=0.1)

apply_market_cap = st.sidebar.checkbox("Filter by Market Cap", value=True)
min_cap = st.sidebar.number_input("Min Market Cap ($B)", 0.0, 500.0, 0.0, 0.1) * 1e9
max_cap = st.sidebar.number_input("Max Market Cap ($B)", 0.1, 500.0, 10.0, 0.1) * 1e9

apply_de_ratio = st.sidebar.checkbox("Max Debt/Equity Ratio", value=False)
max_de_ratio = st.sidebar.number_input("Max D/E Ratio", 0.0, 10.0, 1.0, 0.1)

show_charts = st.sidebar.checkbox("Show Price Charts (1Y)", value=False)
show_trials = st.sidebar.checkbox("Show Clinical Trial Summary", value=False)

if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

@st.cache_data(show_spinner=False)
def fetch_data(tickers, threshold, min_cap, max_cap, apply_market_cap, apply_de_ratio, max_de_ratio):
    results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            price = info.get("currentPrice")
            shares_outstanding = info.get("sharesOutstanding")
            total_cash = info.get("totalCash")
            market_cap = info.get("marketCap")
            de_ratio = info.get("debtToEquity")
            name = info.get("shortName", "N/A")
            sector = info.get("sector", "N/A")

            if all([price, shares_outstanding, total_cash, market_cap]):
                cash_per_share = total_cash / shares_outstanding
                if cash_per_share >= threshold * price:
                    if apply_market_cap and (market_cap < min_cap or market_cap > max_cap):
                        continue
                    if apply_de_ratio and de_ratio is not None and de_ratio > max_de_ratio:
                        continue
                    results.append({
                        "Ticker": ticker,
                        "Company": name,
                        "Sector": sector,
                        "Price": price,
                        "Cash/Share": round(cash_per_share, 2),
                        "Market Cap": market_cap,
                        "Debt/Equity": round(de_ratio, 2) if de_ratio else None
                    })
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            continue
    return pd.DataFrame(results)

def fetch_clinical_trials(company_name):
    try:
        base_url = "https://clinicaltrials.gov/api/query/study_fields"
        fields = "Phase,Status,PrimaryCompletionDate"
        params = {
            "expr": company_name,
            "fields": fields,
            "min_rnk": 1,
            "max_rnk": 100,
            "fmt": "json"
        }
        response = requests.get(base_url, params=params)
        data = response.json()
        studies = data.get("StudyFieldsResponse", {}).get("StudyFields", [])

        phase_count = {}
        upcoming_dates = []

        for study in studies:
            phases = study.get("Phase", [])
            status = study.get("Status", ["N/A"])[0]
            date = study.get("PrimaryCompletionDate", [""])[0]

            for phase in phases:
                if phase:
                    phase_count[phase] = phase_count.get(phase, 0) + 1

            if date and date != "":
                upcoming_dates.append(date)

        return {
            "Total Trials": len(studies),
            "Phases": phase_count,
            "Upcoming Dates": upcoming_dates[:3]
        }
    except Exception as e:
        return {"error": str(e)}

# Auto-run screener
st.subheader("📊 Screening Results")
with st.spinner("🔍 Running biotech screener..."):
    df = fetch_data(biotech_tickers, threshold, min_cap, max_cap, apply_market_cap, apply_de_ratio, max_de_ratio)

if not df.empty:
    st.success(f"Found {len(df)} undervalued biotech companies!")
    for i, row in df.iterrows():
        with st.expander(f"{row['Ticker']} — {row['Company']} | Price: ${row['Price']} | Cash/Share: ${row['Cash/Share']}"):
            st.write(f"Sector: {row['Sector']}, Market Cap: {row['Market Cap']:,}")
            if show_trials:
                trials = fetch_clinical_trials(row['Company'])
                if "error" in trials:
                    st.info("ClinicalTrials.gov lookup failed.")
                else:
                    st.markdown(f"- Total Trials: {trials['Total Trials']}")
                    st.markdown(f"- Trial Phases: {trials['Phases']}")
                    st.markdown(f"- Upcoming Dates: {', '.join(trials['Upcoming Dates'])}")
            if st.button(f"➕ Add {row['Ticker']}", key=row['Ticker']):
                if row['Ticker'] not in [item['Ticker'] for item in st.session_state.watchlist]:
                    st.session_state.watchlist.append(row.to_dict())

    st.download_button("📥 Download Screener CSV", df.to_csv(index=False), "undervalued_biotechs.csv")

    if show_charts:
        st.subheader("📉 1-Year Price Charts")
        for ticker in df['Ticker']:
            st.markdown(f"**{ticker}**")
            try:
                hist = yf.Ticker(ticker).history(period="1y")
                if not hist.empty:
                    fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name=ticker)])
                    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=300)
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Chart error for {ticker}: {e}")
else:
    st.warning("No companies met the criteria.")

# Watchlist section
st.subheader("⭐ My Watchlist")
if st.session_state.watchlist:
    watchlist_df = pd.DataFrame(st.session_state.watchlist)
    st.dataframe(watchlist_df)
    st.download_button("📥 Download Watchlist CSV", watchlist_df.to_csv(index=False), "my_watchlist.csv")
    if st.button("🗑️ Clear Watchlist"):
        st.session_state.watchlist.clear()
else:
    st.info("Your watchlist is empty. Add companies from the screener above.")
