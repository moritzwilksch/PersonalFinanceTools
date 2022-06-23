#%%
import numpy as np
import pandas as pd
import toml
import yfinance as yf
from rich.progress import track

from src.utils.log import log

#%%
data = toml.load("config/holdings.toml")


df = pd.DataFrame(data["stocks"]["ibkr"])
yf_tickers = yf.Tickers(df["ticker"].to_list())

#%%
# yf_tickers.download(period="2y", interval="3mo")

#%%


class DataLoader:
    def __init__(
        self,
        portfolio_name: str,
        holdings_path: str = "config/holdings.toml",
    ) -> None:
        data = toml.load(holdings_path)
        df = pd.DataFrame(data["stocks"][portfolio_name])
        self.yf_tickers = yf.Tickers(df["ticker"].to_list())

    def _get_avg_historical_dividend(self, yf_ticker: yf.Ticker):
        dividends = yf_ticker.dividends
        if len(dividends) == 0:
            log.warning(f"No data found for {yf_ticker.ticker}")
            return 0.0
        dividends = dividends.to_frame().reset_index()

        avg_dividend_per_year = dividends.groupby(dividends["Date"].dt.year).mean()

        if avg_dividend_per_year.empty:
            log.warning(
                f"Dataframe of avg dividend per year is empty for ticker {yf_ticker.ticker}."
            )
            return 0.0

        if len(avg_dividend_per_year) == 1:
            log.warning(
                f"Only have one year worth of data. Estimate might be biased for ticker {yf_ticker.ticker}."
            )

        try:
            # use current year and previous year avg
            return avg_dividend_per_year.iloc[-2:].mean().tolist()[0]
        except:
            log.warning(
                f"Could not calculate 2-year average for ticker {yf_ticker.ticker}."
            )
            return 0.0

    def create_dividends_list(self):
        dividends = []
        for ticker in track(self.yf_tickers.tickers.values()):
            dividend = self._get_avg_historical_dividend(ticker)
            dividends.append({ticker.ticker: dividend})

        print(dividends)


dl = DataLoader("ibkr")
dl.create_dividends_list()
