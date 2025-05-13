import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Biotech Screener — Resilient Trials", layout="wide")
st.title("🧬 Biotech Screener — Charts + Resilient Clinical Trials")

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
                results.append({
                    "Ticker": ticker,
                    "Company": name,
                    "Price": price,
                    "Cash/Share": round(cps, 2)
                })
        except Exception as e:
            skipped.append({"Ticker": ticker, "Error": str(e)})

    return pd.DataFrame(results), pd.DataFrame(skipped)

def fetch_clinical_trials(company_name, ticker):
    try:
        expr = f"{ticker} OR {company_name}"
        base_url = "https://clinicaltrials.gov/api/query/study_fields"
        params = {
            "expr": expr,
            "fields": "Phase,Status,PrimaryCompletionDate",
            "min_rnk": 1,
            "max_rnk": 100,
            "fmt": "json"
        }
        response = requests.get(base_url, params=params, timeout=10)

        if response.status_code != 200:
            return {"error": f"API returned status {response.status_code}"}

        try:
            data = response.json()
        except Exception:
            return {"error": "Invalid JSON response from ClinicalTrials.gov"}

        studies = data.get("StudyFieldsResponse", {}).get("StudyFields", [])
        if not studies:
            return {"error": f"No studies found for query: {expr}"}

        phase_count = {}
        upcoming_dates = []

        for study in studies:
            for phase in study.get("Phase", []):
                if phase:
                    phase_count[phase] = phase_count.get(phase, 0) + 1
            date = study.get("PrimaryCompletionDate", [""])[0]
            if date:
                upcoming_dates.append(date)

        return {
            "Total Trials": len(studies),
            "Phases": phase_count,
            "Upcoming Dates": upcoming_dates[:3]
        }
    except Exception as e:
        return {"error": str(e)}

with st.spinner("Running screener..."):
    df, skipped_df = screen_stocks(tickers)

if not df.empty:
    st.success(f"{len(df)} companies matched.")
    st.dataframe(df)
    st.download_button("📥 Download Results", df.to_csv(index=False), "biotech_matches.csv")

    for _, row in df.iterrows():
        with st.expander(f"{row['Ticker']} — {row['Company']} | Cash/Share: ${row['Cash/Share']}"):
            st.write(f"📈 Price: ${row['Price']}")
            if show_trials:
                with st.spinner(f"Looking up trials for {row['Company']}..."):
                    trials = fetch_clinical_trials(row['Company'], row['Ticker'])
                if "error" in trials:
                    st.error(trials["error"])
                else:
                    st.write(f"🧪 Total Trials: {trials['Total Trials']}")
                    st.write(f"📊 Trial Phases: {trials['Phases']}")
                    st.write(f"📅 Upcoming Completion Dates: {', '.join(trials['Upcoming Dates'])}")

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
    with st.expander("🔍 Skipped Tickers (Missing or Invalid Data)"):
        st.dataframe(skipped_df)
        st.download_button("📄 Download Skipped", skipped_df.to_csv(index=False), "skipped_tickers.csv")
