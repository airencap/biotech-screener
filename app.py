import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Biotech Screener — With Charts", layout="wide")
st.title("🧬 Biotech Screener — With Price Charts")

@st.cache_data
def load_tickers_from_csv():
    return pd.read_csv("biotech_tickers.csv")["Ticker"].tolist()

tickers = load_tickers_from_csv()
threshold = st.sidebar.number_input("Cash/Share ≥ Price (multiple)", 0.0, 5.0, 1.0, 0.1)
show_charts = st.sidebar.checkbox("📈 Show 1-Year Price Charts", value=True)

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

with st.spinner("Running screener..."):
    df, skipped_df = screen_stocks(tickers)

if not df.empty:
    st.success(f"{len(df)} companies matched.")
    st.dataframe(df)
    st.download_button("📥 Download Results", df.to_csv(index=False), "biotech_matches.csv")

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
