
import streamlit as st
import pandas as pd
import yfinance as yf

st.title("🧬 Undervalued US Biotech Screener")
st.markdown("""
This app scans a preloaded list of **US-listed biotech companies** and identifies those where:

**Cash per Share ≥ Current Stock Price**

Great for spotting deep value or potential arbitrage in small caps.
""")

# Load cached CSV list of biotech tickers
@st.cache_data(show_spinner=False)
def load_biotech_tickers():
    # Simulated CSV load (replace with actual file or URL)
    data = {
        "Ticker": ["BIIB", "VRTX", "REGN", "IONS", "NBIX", "SAGE", "ARWR", "ALNY", "BLUE"],
        "Company": [
            "Biogen Inc.", "Vertex Pharmaceuticals", "Regeneron Pharmaceuticals",
            "Ionis Pharmaceuticals", "Neurocrine Biosciences", "Sage Therapeutics",
            "Arrowhead Pharmaceuticals", "Alnylam Pharmaceuticals", "bluebird bio"
        ],
        "Sector": ["Biotechnology"] * 9
    }
    return pd.DataFrame(data)

biotech_df = load_biotech_tickers()
tickers = biotech_df["Ticker"].tolist()

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
df = fetch_data(tickers, threshold)

if not df.empty:
    st.success(f"Found {len(df)} undervalued biotech companies!")
    st.dataframe(df)
    st.download_button("📥 Download CSV", df.to_csv(index=False), "undervalued_biotechs.csv")
else:
    st.warning("No companies met the criteria.")
