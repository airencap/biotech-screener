import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import re

st.set_page_config(page_title="Biotech Screener — Modern Trials", layout="wide")
st.title("🧬 Biotech Screener — Price Charts + Modern ClinicalTrials.gov API")

@st.cache_data
def load_tickers_from_csv():
    return pd.read_csv("biotech_tickers.csv")["Ticker"].tolist()

tickers = load_tickers_from_csv()
threshold = st.sidebar.number_input("Cash/Share ≥ Price (multiple)", 0.0, 5.0, 1.0, 0.1)
show_charts = st.sidebar.checkbox("📈 Show 1-Year Price Charts", value=True)
show_trials = st.sidebar.checkbox("🧪 Show Clinical Trials Data", value=False)

@st.cache_data(show_spinner=True)
def screen_stocks(tickers):
    results = []
    skipped = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            price = info.get("currentPrice")
            cash = info.get("totalCash")
            shares = info.get("sharesOutstanding")
            name = info.get("shortName", ticker)
            if not all([price, cash, shares]):
                skipped.append({"Ticker": ticker, "Price": price, "Cash": cash, "Shares": shares})
                continue
            cps = cash / shares
            if cps >= price * threshold:
                results.append({"Ticker": ticker, "Company": name, "Price": price, "Cash/Share": round(cps, 2)})
        except Exception as e:
            skipped.append({"Ticker": ticker, "Error": str(e)})
    return pd.DataFrame(results), pd.DataFrame(skipped)

def fetch_clinical_trials(expr):
    # Modern ClinicalTrials.gov API v2
    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.cond": expr,
        "pageSize": 100,
        "format": "json",
        "countTotal": "true"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {"Total Trials": 0, "Phases": {}, "Upcoming Dates": [], "error": str(e)}
    total = data.get("totalCount", 0)
    studies = data.get("studies", [])
    phase_count = {}
    upcoming = []
    for study in studies:
        status_mod = study.get("protocolSection", {}).get("statusModule", {})
        # phases
        for phase_item in status_mod.get("phaseList", []):
            phase = phase_item.get("phase")
            if phase:
                phase_count[phase] = phase_count.get(phase, 0) + 1
        # primary completion date
        date = status_mod.get("primaryCompletionDateStruct", {}).get("date")
        if date:
            upcoming.append(date)
    return {"Total Trials": total, "Phases": phase_count, "Upcoming Dates": upcoming[:3]}

def get_trial_info(company_name, ticker):
    company_clean = re.sub(r'[\\/:*?"<>|]', "", company_name)
    trials = fetch_clinical_trials(company_clean)
    if trials.get("Total Trials", 0) == 0:
        trials = fetch_clinical_trials(ticker)
    return trials

with st.spinner("Running screener..."):
    df, skipped_df = screen_stocks(tickers)

if not df.empty:
    st.success(f"{len(df)} companies matched.")
    st.dataframe(df)
    st.download_button("📥 Download Results", df.to_csv(index=False), "results.csv")

    for _, row in df.iterrows():
        with st.expander(f"{row['Ticker']} — {row['Company']} | Cash/Share: ${row['Cash/Share']}"):
            st.write(f"📈 Price: ${row['Price']}")
            if show_trials:
                trials = get_trial_info(row['Company'], row['Ticker'])
                st.write(f"🧪 Total Trials: {trials.get('Total Trials',0)}")
                st.write(f"📊 Trial Phases: {trials.get('Phases',{})}")
                st.write(f"📅 Upcoming Completion Dates: {', '.join(trials.get('Upcoming Dates',[]))}")
    if show_charts:
        st.subheader("📉 1-Year Price Charts")
        for ticker in df["Ticker"]:
            try:
                hist = yf.Ticker(ticker).history(period="1y")
                if not hist.empty:
                    fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name=ticker)])
                    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=300)
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Chart error for {ticker}: {e}")
else:
    st.warning("No matches found.")

if not skipped_df.empty:
    with st.expander("🔍 Skipped Tickers"):
        st.dataframe(skipped_df)
        st.download_button("📄 Download Skipped", skipped_df.to_csv(index=False), "skipped.csv")
