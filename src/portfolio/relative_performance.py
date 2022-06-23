#%%
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import yfinance as yf
from IPython.display import set_matplotlib_formats

set_matplotlib_formats("pdf", "svg")

#%%
tickers = [
    # "JEPI",
    # "SCHD",
    # "SPYD",
    "DIVO",
    # "SPHD",
    "DGRO"
    # "VYM",
    # "VIG"
]
data = yf.Tickers(tickers).history("5y")[["Dividends", "Close"]]
close, divis = data["Close"], data["Dividends"]

#%%
missing = close.isna().any(axis=1)
close, divis = close[~missing], divis[~missing]

#%%
close_divs_reinvested = close + divis.cumsum()
close = close / close.iloc[0]
close_divs_reinvested = close_divs_reinvested / close_divs_reinvested.iloc[0]

#%%
plot_close = close.reset_index().melt(var_name="ticker", id_vars="Date")
plot_close_divs_reinvested = close_divs_reinvested.reset_index().melt(
    var_name="ticker", id_vars="Date"
)

#%%
fig, ax = plt.subplots(figsize=(15, 8))
sns.lineplot(data=plot_close, y="value", hue="ticker", x="Date", ax=ax)
sns.despine()

#%%
fig, ax = plt.subplots(figsize=(15, 8))
sns.lineplot(data=plot_close_divs_reinvested, y="value", hue="ticker", x="Date", ax=ax)
sns.despine()
