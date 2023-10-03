# %%
import matplotlib.pyplot as plt
import pandas as pd
import polars as pl
import seaborn as sns
import yfinance as yf
from IPython.display import set_matplotlib_formats

set_matplotlib_formats("pdf", "svg")

# %%
tickers = [
    # "JEPI",
    # "JEPQ",
    "SCHD",
    # "SPYD",
    "DIVO",
    # "SPHD",
    "DGRO",
    # "VYM",
    "VIG"
    # "COWZ",
]
data = yf.Tickers(tickers).history("7y")[["Dividends", "Close"]]
close, divis = data["Close"], data["Dividends"]

# %%
missing = close.isna().any(axis=1)
close, divis = close[~missing], divis[~missing]

# %%
yoy_performance = (
    pl.from_pandas(close, include_index=True)
    .with_columns(
        (pl.col(tickers).pct_change() + 1).cumprod().over(pl.col("Date").dt.year())
    )
    .group_by(pl.col("Date").dt.year())
    .agg(pl.col(tickers).last())
)
print(yoy_performance)

# %%
fig, ax = plt.subplots(figsize=(13, 6))
sns.pointplot(
    data=yoy_performance.melt(id_vars=["Date"]).to_pandas(),
    x="Date",
    y="value",
    hue="variable",
    ax=ax
)
# %%
close_divs_reinvested = close + divis.cumsum()
close = close / close.iloc[0]
close_divs_reinvested = close_divs_reinvested / close_divs_reinvested.iloc[0]

# %%
plot_close = close.reset_index().melt(var_name="ticker", id_vars="Date")
plot_close_divs_reinvested = close_divs_reinvested.reset_index().melt(
    var_name="ticker", id_vars="Date"
)

# %%
fig, ax = plt.subplots(figsize=(13, 6))
sns.lineplot(data=plot_close, y="value", hue="ticker", x="Date", ax=ax)
sns.despine()

# %%
fig, ax = plt.subplots(figsize=(13, 6))
sns.lineplot(data=plot_close_divs_reinvested, y="value", hue="ticker", x="Date", ax=ax)
sns.despine()
