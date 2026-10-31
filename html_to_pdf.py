#!/usr/bin/env python3
"""Turn life-in-the-uk-print.html into an A4 PDF.

The page size and margins come from the @page rule in that HTML file.
Run with the project virtualenv:

    .venv/bin/python html_to_pdf.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "life-in-the-uk-print.html"
OUTPUT = ROOT / "life-in-the-uk-print.pdf"


def main() -> None:
    if not SOURCE.is_file():
        sys.exit(f"Missing {SOURCE.name}. Run: python3 build_print.py")

    try:
        from weasyprint import HTML
    except ImportError:
        sys.exit(
            "WeasyPrint is not installed. From this folder, run:\n"
            "  uv venv .venv && uv pip install --python .venv/bin/python weasyprint"
        )

    document = HTML(filename=SOURCE).render()
    document.write_pdf(OUTPUT)
    pages = len(document.pages)
    print(f"Wrote {pages} A4 page{'s' if pages != 1 else ''} to {OUTPUT}")


if __name__ == "__main__":
    main()
