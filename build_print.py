#!/usr/bin/env python3
"""Build a compact A4 print view from README.md."""

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "README.md"
OUTPUT = ROOT / "life-in-the-uk-print.html"

WIDE_HEADERS = {"country", "type of courts", "name"}


def inline(text: str) -> str:
    text = html.escape(text.strip())
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return text


def clean_key(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^_(.+)_$", r"\1", text)
    return text


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def is_separator(line: str) -> bool:
    cells = split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def heading(line: str) -> tuple[int, str] | None:
    match = re.match(r"^(#{2,3})\s+(.*?)\s*#*\s*$", line)
    if not match:
        return None
    return len(match.group(1)), match.group(2).strip()


def render_compact(rows: list[list[str]]) -> str:
    header = [cell.lower() for cell in rows[0]]
    body = rows[1:]
    person = header[:1] == ["name"]
    css = "entry person" if person else "entry"
    parts = ['<div class="sheet">']
    for row in body:
        cells = [clean_key(cell) for cell in row]
        while len(cells) < 3:
            cells.append("")
        key, main, extra = cells[0], cells[1], cells[2]
        if not key and not main:
            continue
        bits = []
        if main:
            bits.append(f"<strong>{inline(main)}</strong>" if not person else inline(main))
        if extra and extra not in {"-", "–"}:
            bits.append(inline(extra))
        detail = " — ".join(bits) if bits else ""
        if person:
            label = f"<strong>{inline(key)}</strong>"
        else:
            label = inline(key)
        parts.append(
            f'<div class="{css}"><span class="key">{label}</span><span>{detail}</span></div>'
        )
    parts.append("</div>")
    return "\n".join(parts)


def render_table(rows: list[list[str]]) -> str:
    width = max(len(row) for row in rows)
    parts = ['<table class="wide">']
    for index, row in enumerate(rows):
        tag = "th" if index == 0 else "td"
        cells = row + [""] * (width - len(row))
        inner = "".join(f"<{tag}>{inline(clean_key(cell))}</{tag}>" for cell in cells)
        parts.append(f"<tr>{inner}</tr>")
    parts.append("</table>")
    return "\n".join(parts)


def render_list(items: list[tuple[int, str]]) -> str:
    html_parts = ["<ul>"]
    open_nested = False
    for index, (level, text) in enumerate(items):
        next_level = items[index + 1][0] if index + 1 < len(items) else 0
        if level == 0 and open_nested:
            html_parts.append("</ul></li>")
            open_nested = False
        if level == 0 and next_level > 0:
            html_parts.append(f"<li>{inline(text)}<ul>")
            open_nested = True
        elif level > 0:
            html_parts.append(f"<li>{inline(text)}</li>")
        else:
            html_parts.append(f"<li>{inline(text)}</li>")
    if open_nested:
        html_parts.append("</ul></li>")
    html_parts.append("</ul>")
    return "\n".join(html_parts)


def parse(text: str) -> str:
    lines = text.splitlines()
    blocks: list[str] = []
    index = 0
    title_done = False

    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()

        if not stripped or stripped == "----":
            index += 1
            continue

        found = heading(raw)
        if found:
            level, title = found
            tag = "h2" if level == 2 else "h3"
            blocks.append(f"<{tag}>{inline(title)}</{tag}>")
            index += 1
            title_done = True
            continue

        if not title_done and not stripped.startswith(("|", "*", ">", "#")):
            blocks.append(f"<h1>{inline(stripped)}</h1>")
            title_done = True
            index += 1
            continue

        if stripped.startswith("|"):
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                if not is_separator(lines[index]):
                    rows.append(split_row(lines[index]))
                index += 1
            if rows:
                header = rows[0][0].lower() if rows[0] else ""
                wide = len(rows[0]) >= 4 or header in {"country", "type of courts"}
                # The government table starts with "Name" but has 5 columns.
                if len(rows[0]) >= 4:
                    wide = True
                blocks.append(render_table(rows) if wide else render_compact(rows))
            continue

        if stripped.startswith(("*", "-")) and not stripped.startswith("---"):
            items: list[tuple[int, str]] = []
            while index < len(lines):
                current = lines[index]
                if not current.strip():
                    break
                match = re.match(r"^(\s*)[*-]\s+(.*)$", current)
                if not match:
                    break
                level = 1 if len(match.group(1)) >= 2 else 0
                items.append((level, match.group(2)))
                index += 1
            blocks.append(render_list(items))
            continue

        if stripped.startswith(">"):
            quote = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote.append(lines[index].strip().lstrip(">").strip())
                index += 1
            blocks.append("<blockquote>" + "<br>".join(inline(line) for line in quote if line) + "</blockquote>")
            continue

        paragraph = [stripped]
        index += 1
        while index < len(lines) and lines[index].strip() and not lines[index].strip().startswith(("|", "#", "*", ">", "-")):
            paragraph.append(lines[index].strip())
            index += 1
        blocks.append(f"<p>{inline(' '.join(paragraph))}</p>")

    return "\n".join(blocks)


STYLE = """
@page {
  size: A4;
  margin: 8mm 7mm 12mm;
  @bottom-right {
    content: counter(page);
    font-family: "Liberation Sans", "Nimbus Sans", Arial, sans-serif;
    font-size: 8pt;
    color: #161616;
  }
}
* { box-sizing: border-box; }
html { color-scheme: light; background: #fff; font: 8pt/1.22 "Liberation Sans", "Nimbus Sans", Arial, sans-serif; color: #161616; }
body { margin: 0; background: #fff; columns: 2; column-gap: 5mm; }
h1 { column-span: all; font-size: 13pt; line-height: 1.15; margin: 0 0 2pt; }
h2 { column-span: all; font-size: 10pt; line-height: 1.2; margin: 8pt 0 3pt; padding-bottom: 1pt; border-bottom: 0.7pt solid #222; break-after: avoid; }
h3 { font-size: 8.6pt; margin: 6pt 0 2pt; break-after: avoid; }
p { column-span: all; margin: 0 0 3pt; }
.sheet { margin: 0 0 4pt; }
.entry { display: grid; grid-template-columns: 18mm 1fr; column-gap: 1.6mm; break-inside: avoid; padding: 1.4pt 0; border-bottom: 0.6pt solid #8a8a8a; }
.entry.person { grid-template-columns: 28mm 1fr; }
.key { font-weight: 700; }
table.wide { column-span: all; width: 100%; border-collapse: collapse; font-size: 7.4pt; line-height: 1.2; margin: 1pt 0 5pt; }
th, td { text-align: left; vertical-align: top; padding: 1pt 3pt 1pt 0; }
th { border-bottom: 0.6pt solid #222; font-weight: 700; }
td { border-bottom: 0.6pt solid #8a8a8a; }
tr { break-inside: avoid; }
ul { margin: 1pt 0 4pt; padding-left: 1.15em; }
li { break-inside: avoid; margin: 0 0 1pt; }
li ul { margin: 1pt 0 1pt; }
blockquote { margin: 2pt 0 4pt; padding-left: 2mm; border-left: 1.5pt solid #222; font-style: italic; break-inside: avoid; }
strong { font-weight: 700; }
"""


def main() -> None:
    body = parse(SOURCE.read_text())
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Life in the United Kingdom</title>
<style>{STYLE}</style>
</head>
<body>
{body}
</body>
</html>
"""
    OUTPUT.write_text(page)
    print(OUTPUT)


if __name__ == "__main__":
    main()
