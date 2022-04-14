from locale import NOEXPR
from turtle import width

from numpy import number
from pylatex import (
    Center,
    Command,
    Document,
    LineBreak,
    NewLine,
    Section,
    Subsection,
    Tabu,
    Tabular,
)
from pylatex.utils import NoEscape, italic


def create_preamble(doc: Document):
    doc.preamble.append(
        Command(
            "renewcommand", arguments=[Command("familydefault"), Command("sfdefault")]
        )
    )
    doc.preamble.append(Command("usepackage", "uarial"))
    doc.preamble.append(
        Command("usepackage", options=["a4paper", "margin=1in"], arguments="geometry")
    )

    return doc


def fill_document(doc: Document):
    with doc.create(Center()):
        # doc.append(NoEscape("{\sffamily"))
        with doc.create(Tabular("ccccc", row_height=1.1, booktabs=True)) as table:
            table.add_hline()
            # table.add_row(Command("textbf", "Attribute"), Command("textbf", "Value"))
            headers = ("Ticker", "Price", "Strike", "Expiration", "DTE")
            values = ("INTC", "$46.12", "44", "2022-05-12", "22")

            table.add_row(*(Command("textbf", x) for x in headers))
            table.add_hline()
            table.add_row(*values)
        # doc.append(NoEscape("}"))

    with doc.create(Subsection("Expected Move", numbering=False)):
        doc.append("Also some crazy characters: $&#{}")

    return doc


def create_title(doc: Document):
    with doc.create(Center()):
        doc.append(NoEscape("{ \LARGE"))
        doc.append(Command("textbf", "Trade Report"))
        doc.append(NoEscape("}"))

    return doc


if __name__ == "__main__":
    # Basic document
    doc = Document("out/basic")

    # Boilerplate
    doc = create_preamble(doc)
    doc = create_title(doc)

    # Sections
    doc = fill_document(doc)

    doc.generate_pdf(clean=True, clean_tex=False)
