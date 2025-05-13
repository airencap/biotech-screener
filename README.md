	•	Loads a list of US biotech tickers (from NASDAQ & NYSE using a biotech filter).
	•	For each ticker:
	•	Pulls total cash, shares outstanding, and stock price using Yahoo Finance API (yfinance).
	•	Calculates cash/share and compares to current price.
	•	Filters and returns:
	•	Only stocks where cash/share >= price.
	•	Outputs a clean table with:
	•	Ticker, Company Name, Sector, Cash/Share, Price, Market Cap
