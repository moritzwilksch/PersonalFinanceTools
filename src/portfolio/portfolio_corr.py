# %%
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import toml
import yfinance as yf

_config = toml.load("config/portfolio.toml")
portfolio_tickers = _config.get("portfolio")
candidates_tickers = _config.get("candidates")

#%%
# portfolio
yf_tickers_portfolio = yf.Tickers(" ".join(portfolio_tickers))
portfolio_prices = yf_tickers_portfolio.history()["Close"]
portfolio_returns = portfolio_prices.pct_change()

fig, axes = plt.subplots(1, 1, figsize=(15, 13))
sns.heatmap(portfolio_returns.corr(), annot=True, ax=axes, cmap="coolwarm")
plt.title("Portfolio Correlation", size=18)


# Candidates
yf_tickers_potentials = yf.Tickers(" ".join(candidates_tickers))
candidates_prices = yf_tickers_potentials.history()["Close"]
candidates_returns = candidates_prices.pct_change()

#%%
fig, axes = plt.subplots(1, 1, figsize=(15, 13))
sns.heatmap(
    pd.concat([portfolio_returns, candidates_returns], axis=1).corr(),
    annot=True,
    ax=axes,
    cmap="coolwarm",
)
plt.title("Portfolio Correlation + CANDIDATES", size=18)
plt.axvline(x=len(portfolio_prices), color="k", linewidth=2.5)
plt.axhline(y=len(portfolio_prices), color="k", linewidth=2.5)
