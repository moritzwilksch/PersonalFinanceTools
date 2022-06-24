#%%
from curses import noecho
from turtle import position
import joblib
import numpy as np
import pandas as pd
import toml
import yfinance as yf
from pylatex import Command, Document, NoEscape, Section, Subsection, Table, Tabular
from regex import P
from rich import print
from rich.progress import track

from src.utils.log import log

#%%
data = toml.load("config/holdings.toml")

df = pd.DataFrame(data["stocks"]["ibkr"])
yf_tickers = yf.Tickers(df["ticker"].to_list())

#%%
# yf_tickers.download(period="2y", interval="3mo")

#%%
USE_CACHE = True


class DataLoader:
    def __init__(
        self,
        portfolio_name: str = None,
        holdings_path: str = "config/holdings.toml",
    ) -> None:
        self.data = toml.load(holdings_path)
        self.HARDCODED_DIVIDENDS = self.data["hardcoded_dividends"]

        if portfolio_name is not None:
            self.portfolio_name = portfolio_name
            self.portfolio = self.data["stocks"][portfolio_name]
            self.position = {
                elem.get("ticker"): elem.get("position") for elem in self.portfolio
            }
            ticker_list = [el.get("ticker") for el in self.portfolio]
            self.yf_tickers = yf.Tickers(ticker_list)

    def _get_avg_historical_dividend(self, yf_ticker: yf.Ticker):
        """
        Pulls average yearly dividend for yf_ticker.

        Args:
            yf_ticker (yf.Ticker): yfinance ticker object

        Returns:
            float: Average yearly dividend of current and previous year.
        """
        dividends = yf_ticker.dividends
        if len(dividends) == 0:
            for elem in self.HARDCODED_DIVIDENDS:
                if elem["ticker"] == yf_ticker.ticker:
                    return elem["dividend"]

            log.warning(f"No data found for {yf_ticker.ticker}")
            return 0.0
        dividends = dividends.to_frame().reset_index()

        dividend_per_year = dividends.groupby(dividends["Date"].dt.year).sum()

        if dividend_per_year.empty:
            log.warning(
                f"Dataframe of avg dividend per year is empty for ticker {yf_ticker.ticker}."
            )
            return 0.0

        try:
            # use current year and previous year avg
            return dividend_per_year.iloc[-2].tolist()[0]
        except:
            log.warning(
                f"Could not index previous years dividend for ticker {yf_ticker.ticker}."
            )
            return 0.0

    def create_dividends_list(self, use_cache: bool = True):
        if use_cache:
            log.info("Using cached information.")
            return joblib.load(f"out/cache/dividends_{self.portfolio_name}.joblib")

        dividends = []
        for ticker in track(self.yf_tickers.tickers.values()):
            dividend = self._get_avg_historical_dividend(ticker)
            dividends.append(
                {
                    "ticker": ticker.ticker,
                    "dividend": dividend,
                    "position": self.position.get(ticker.ticker),
                    "cashflow": self.position.get(ticker.ticker) * dividend,
                }
            )

        joblib.dump(dividends, f"out/cache/dividends_{self.portfolio_name}.joblib")

        return dividends

    def get_crypto_data(self):
        return self.data["crypto"]["positions"]

    def get_p2p_data(self):
        return self.data["p2p"]["positions"]


class Report:
    def __init__(self) -> None:
        self.eurusd = yf.Ticker("EURUSD=X").history("1d").to_numpy().ravel()[0]
        self.PORTFOLIOS = ["ibkr", "degiro", "comdirect"]

    def create_preamble(self, doc: Document):

        doc.preamble.append(Command("usepackage", "charter"))
        doc.preamble.append(Command("usepackage", "parskip"))
        doc.preamble.append(Command("usepackage", "booktabs"))
        # doc.preamble.append(Command("usepackage", "float"))
        doc.preamble.append(Command("usepackage", "geometry", ["a4paper", "margin=1in"]))

        doc.append(Command("title", NoEscape("\\vspace{-3em} Passive Income Report")))
        doc.append(Command("date", NoEscape("\\vspace{-3em}\\today")))
        doc.append(Command("maketitle"))

    def create_table_from_dividends(self, doc: Document, dividends: list):

        with doc.create(Table(position="!ht")) as t:
            t.append(Command("centering"))

            with t.create(Tabular(table_spec="lcccc", booktabs=False)) as tab:
                tab.append(Command("toprule"))
                tab.add_row(
                    [
                        Command("textbf", "Ticker"),
                        Command("textbf", "Annual Dividend"),
                        Command("textbf", "Position"),
                        Command("textbf", "Yearly Cashflow"),
                        Command("textbf", "Monthly Cashflow"),
                    ]
                )
                tab.append(Command("midrule"))

                for elem in dividends:
                    tab.add_row(
                        [
                            elem["ticker"],
                            f"${elem['dividend']:7.2f}",
                            elem["position"],
                            f"${elem['cashflow']:7.2f}",
                            f"${elem['cashflow'] / 12:7.2f}",
                        ]
                    )

                tab.append(Command("midrule"))
                total_yearly = sum(elem["cashflow"] for elem in dividends)
                tab.add_row(
                    [
                        NoEscape("$\Sigma$"),
                        "-",
                        "-",
                        f"${total_yearly:7.2f}",
                        f"${total_yearly/12:7.2f}",
                    ]
                )
                tab.append(Command("bottomrule"))

    def add_summary_section(self, doc: Document):
        doc.append(Section("Summary"))

        cash_flows = dict()  # map: portfolioname -> yearly CF
        for portfolio in self.PORTFOLIOS:
            dividends = DataLoader(portfolio).create_dividends_list(use_cache=USE_CACHE)
            cash_flows[portfolio] = sum(ele["cashflow"] for ele in dividends)

        cash_flows["p2p"] = sum(
            [
                pos["investment"] * self.eurusd * pos["apr"]
                for pos in DataLoader().get_p2p_data()
            ]
        )

        cash_flows["crypto"] = sum(
            [pos["investment"] * pos["apr"] for pos in DataLoader().get_crypto_data()]
        )

        with doc.create(Table(position="!ht")) as t:
            t.append(Command("centering"))

            with t.create(Tabular(table_spec="lccc", booktabs=False)) as tab:
                tab.append(Command("toprule"))
                tab.add_row(
                    [
                        Command("textbf", "Currency"),
                        Command("textbf", "Yearly Cashflow"),
                        Command("textbf", "Monthly Cashflow"),
                        Command("textbf", "Daily Cashflow"),
                    ]
                )
                tab.append(Command("midrule"))

                yearly_cf = sum(cash_flows.values())

                tab.add_row(
                    [
                        "USD",
                        f"${yearly_cf:8.2f}",
                        f"${yearly_cf / 12:8.2f}",
                        f"${yearly_cf/12/31:8.2f}",
                    ]
                )

                tab.add_row(
                    [
                        "EUR",
                        f"€{1/self.eurusd * yearly_cf:8.2f}",
                        f"€{1/self.eurusd * yearly_cf / 12:8.2f}",
                        f"€{1/self.eurusd * yearly_cf/12/31:8.2f}",
                    ]
                )
                tab.append(Command("bottomrule"))

                disclaimer = f"EUR/USD rate = {self.eurusd:.3f}, summing cashflow from {', '.join(cash_flows.keys())}"
                tab.append(Command("multicolumn", [4, "c",  NoEscape(f"\\footnotesize {disclaimer}")]))

    def add_stocks_section(self, doc: Document):
        # doc.append(Command("newpage"))
        PAGEBREAK_AFTER = ["ibkr", "comdirect"]
        doc.append(Section("Stocks and Equities"))

        for portfolio in self.PORTFOLIOS:
            dl = DataLoader(portfolio)
            dividends = dl.create_dividends_list(use_cache=True)
            dividends.sort(key=lambda e: e["cashflow"] * -1)

            doc.append(Subsection(f"Portfolio: {portfolio.upper()}"))
            self.create_table_from_dividends(doc, dividends)

            if portfolio in PAGEBREAK_AFTER:
                doc.append(Command("newpage"))

    def create_table_for_other_investment(
        self, doc: Document, data: list, convert_eur_to_usd: bool
    ):
        data.sort(key=lambda x: x["investment"] * x["apr"] * -1)

        all_cashflows = []
        with doc.create(Table(position="!ht")) as t:
            t.append(Command("centering"))

            with t.create(Tabular(table_spec="lcccc", booktabs=False)) as tab:
                tab.append(Command("toprule"))
                tab.add_row(
                    [
                        Command("textbf", "Platform"),
                        Command("textbf", "Investment"),
                        Command("textbf", "APR"),
                        Command("textbf", "Yearly Cashflow"),
                        Command("textbf", "Monthly Cashflow"),
                    ]
                )
                tab.append(Command("midrule"))

                currency_conversion = self.eurusd if convert_eur_to_usd else 1.0

                for position in data:
                    investment = position["investment"] * currency_conversion
                    apr = position["apr"]
                    cashflow = investment * apr
                    all_cashflows.append(cashflow)
                    tab.add_row(
                        [
                            position["platform"],
                            f"${investment:7.2f}",
                            f"{apr:.1%}",
                            f"${cashflow:7.2f}",
                            f"${cashflow / 12:7.2f}",
                        ]
                    )
            tab.append(Command("midrule"))
            tab.add_row(
                [
                    NoEscape("$\Sigma$"),
                    "-",
                    "-",
                    f"${sum(all_cashflows):7.2f}",
                    f"${sum(all_cashflows)/12:7.2f}",
                ]
            )
            tab.append(Command("bottomrule"))

    def add_p2p_section(self, doc: Document):
        doc.append(Section("P2P Lending"))
        data = DataLoader().get_p2p_data()
        self.create_table_for_other_investment(doc, data=data, convert_eur_to_usd=True)

    def add_crypto_section(self, doc: Document):
        doc.append(Section("Crypto Staking"))
        data = DataLoader().get_crypto_data()
        self.create_table_for_other_investment(doc, data=data, convert_eur_to_usd=False)

    def create(self):
        doc = Document("basic", document_options="8pt")
        self.create_preamble(doc)
        self.add_summary_section(doc)
        self.add_stocks_section(doc)
        self.add_p2p_section(doc)
        self.add_crypto_section(doc)
        doc.generate_pdf("out/report/report", clean_tex=False)


r = Report()
r.create()
