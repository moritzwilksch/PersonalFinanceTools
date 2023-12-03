# %%
import seaborn as sns
from matplotlib import pyplot as plt
import yfinance as yf
import polars as pl


# %%
class Portfolio:
    def __init__(self, tickers: list[str]) -> None:
        self.tickers = tickers
        _yf_data = yf.Tickers(tickers).history(
            period="max", interval="1d", group_by="ticker"
        )

        # init data
        self.data = {
            tick: pl.from_pandas(_yf_data[tick], include_index=True)
            for tick in self.tickers
        }
        self.data = {
            tick: data.rename(
                {c: c.lower().replace(" ", "_") for c in data.columns}
            ).sort("date")
            for tick, data in self.data.items()
        }

        # calc min common date
        self.min_common_date = max(
            [data.drop_nulls("close")["date"].min() for data in self.data.values()]
        ).date()

    def plot_history(self, reinvest_dividends: bool = False):
        fig, ax = plt.subplots(figsize=(12, 6))
        palette = sns.color_palette("husl", len(self.tickers))

        for idx, (tick, data) in enumerate(self.data.items()):
            _data_filtered = data.filter(pl.col("date") >= self.min_common_date)

            if reinvest_dividends:
                _data_filtered = _data_filtered.with_columns(
                    pl.col("close") + pl.col("dividends").cum_sum()
                )

            sns.lineplot(
                data=_data_filtered.with_columns(
                    close_normalized=pl.col("close") / pl.col("close").first()
                ),
                x="date",
                y="close_normalized",
                ax=ax,
                label=tick,
                color=palette[idx],
            )

        ax.legend()
        ax.set_title(
            f"Portfolio History (dividends {'NOT ' if not reinvest_dividends else ''}reinvested)"
        )
        sns.despine()

    def plot_correlation(self):
        common_data = pl.DataFrame(
            {
                tick: data.filter(pl.col("date") >= self.min_common_date)["close"]
                for tick, data in self.data.items()
            }
        )

        correlation_matrix = (
            common_data.with_columns(pl.all().pct_change()).drop_nulls().corr()
        )
        sns.heatmap(
            correlation_matrix,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            cbar=False,
            square=True,
        )


portfolio = Portfolio(
    [
        # "JEPQ",
        "DIVO",
        "DGRO",
        "SCHD",
    ]
)
portfolio.plot_history(reinvest_dividends=False)
portfolio.plot_correlation()
