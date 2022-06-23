import datetime

import toml
import yfinance as yf
from pylatex import Center, Command, Document, Figure, Subsection, Tabular, TextColor
from pylatex.utils import NoEscape, italic


def create_preamble(doc: Document):
    """Creates document preamble"""
    doc.preamble.append(
        Command(
            "renewcommand", arguments=[Command("familydefault"), Command("sfdefault")]
        )
    )
    # doc.preamble.append(Command("usepackage", "uarial"))
    doc.preamble.append(
        Command("usepackage", options=["a4paper", "margin=1in"], arguments="geometry")
    )
    doc.preamble.append(Command("usepackage", "xcolor"))

    return doc


def fill_document(doc: Document, ticker: str, dte: int):
    """Fills document with content"""
    yf_ticker = yf.Ticker(ticker)
    price = yf_ticker.history("1d")["Close"].to_list()[-1]
    expiration = datetime.datetime.today() + datetime.timedelta(days=dte)

    with doc.create(Center()):
        # doc.append(NoEscape("{\sffamily"))
        with doc.create(Tabular("cc|cc", row_height=1.1, booktabs=True)) as table:
            table.add_hline()
            # table.add_row(Command("textbf", "Attribute"), Command("textbf", "Value"))
            headers = ("Ticker", "Last Price", "Expiration", "DTE")
            values = (ticker, f"${price:.2f}", f"{expiration:%Y-%m-%d}", dte)

            table.add_row(*(Command("textbf", x) for x in headers))
            table.add_hline()
            table.add_row(*values)
        # doc.append(NoEscape("}"))

    with doc.create(Subsection("Expected Move", numbering=False)):
        with doc.create(Figure(position="h!")) as fig:
            fig.add_image(filename="expected_move.png", width="500px")

    with doc.create(
        Subsection("Expected Move - Historic Reliability", numbering=False)
    ):
        with doc.create(Figure(position="h!")) as fig:
            fig.add_image(filename="expected_move_reliability.png", width="500px")

    return doc


def create_title(doc: Document):
    with doc.create(Center()):
        doc.append(NoEscape("{ \LARGE"))
        doc.append(TextColor("blue", Command("textbf", "Expected Movement Report")))
        doc.append(NoEscape("}"))

    return doc


if __name__ == "__main__":
    config = toml.load("config/shortput.toml")
    TICKER = config.get("TICKER")
    DTE = config.get("DTE")

    # Basic document
    doc = Document("out/shortput_report")

    # Boilerplate
    doc = create_preamble(doc)
    doc = create_title(doc)

    # Sections
    doc = fill_document(doc, ticker=TICKER, dte=DTE)

    doc.generate_pdf(clean=True, clean_tex=True)
