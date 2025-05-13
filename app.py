import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Biotech Screener — CSV Mode", layout="wide")
st.title("🧬 Biotech Screener — Using Static Ticker List")

# Load ticker list from a local CSV
@st.cache_data
def load_tickers_from_csv():
    return pd.read_csv("biotech_tickers.csv")["Ticker"].tolist()

tickers = load_tickers_from_csv()

threshold = st.sidebar.number_input("Cash/Share ≥ Price (multiple)", 0.0, 5.0, 1.0, 0.1)

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
                skipped.append({
                    "Ticker": ticker,
                    "Price": price,
                    "Cash": cash,
                    "Shares": shares
                })
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

with st.spinner("Running screener..."):
    df, skipped_df = screen_stocks(tickers)

if not df.empty:
    st.success(f"{len(df)} companies matched.")
    st.dataframe(df)
    st.download_button("📥 Download Results", df.to_csv(index=False), "biotech_matches.csv")
else:
    st.warning("No matches found.")

if not skipped_df.empty:
    with st.expander("🔍 Skipped Tickers (Missing or Invalid Data)"):
        st.dataframe(skipped_df)
        st.download_button("📄 Download Skipped", skipped_df.to_csv(index=False), "skipped_tickers.csv")
