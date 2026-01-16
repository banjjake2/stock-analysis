# Stock Financial Analysis App

This is a Streamlit app for analyzing stock financial data using the Financial Modeling Prep (FMP) API.

## Features

- Fetch income statement data for the last 5 years
- Display key metrics: date, revenue, operating income, EPS, net income
- Visualize revenue and operating income trends with bar charts
- Dark mode theme inspired by Finviz
- Error handling for API failures and invalid tickers

## Installation

1. Clone or download this repository.
2. Install the required libraries:
   ```
   pip install -r requirements.txt
   ```
3. Get an API key from [Financial Modeling Prep](https://financialmodelingprep.com/).

## Usage

Run the app:
```
streamlit run app.py
```

On first run, enter your FMP API Key in the input field and click "Set API Key". The key is stored securely in the session and will be required again if you restart the app.

## Usage

Run the app:
```
streamlit run app.py
```

Enter your API key and a stock ticker (e.g., NVDA, AAPL), then click "Load Data" or it will load automatically.

## Requirements

- Python 3.7+
- streamlit
- requests
- pandas
- plotly