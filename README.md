# 🧬 Biotech Undervalued Stock Screener (Streamlit App)

This is a fully-featured Streamlit web app for scanning **US-listed biotech companies** that may be undervalued based on key financial metrics.

## 🔍 Features

- **Cash/Share ≥ Price** screening
- **Market Cap filter**
- **Debt/Equity filter**
- **ClinicalTrials.gov API integration**
  - Total trials
  - Phase breakdown
  - Upcoming completion dates
- **Interactive Price Charts** (1Y)
- **Watchlist management**
- **Dark mode toggle**
- **Loading spinners + expandable views**
- Live biotech ticker list scraped from Finviz

## 🚀 Getting Started

1. **Clone or upload this repo to [Streamlit Cloud](https://streamlit.io/cloud)**.
2. Make sure the following files are in your repo:
   - `biotech_screener_final_app.py` → Rename to `app.py`
   - `requirements.txt`

3. Deploy your app using Streamlit’s “New App” interface.

## 📦 Installation (Local)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🧠 Powered By

- `Streamlit` for UI
- `yfinance` for financial data
- `Finviz` for biotech ticker scraping
- `ClinicalTrials.gov API` for trial insights
- `plotly` for charting

## 📝 License

MIT — feel free to adapt or extend!

---

Made with 💡 by [Your Name]
