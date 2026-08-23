from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "group_meeting_2026-08-18"
SOURCE = REPORT_DIR / "report_readable_cn.md"
TARGET = REPORT_DIR / "report.html"


CSS = """
:root {
  color-scheme: light;
  --fg: #162033;
  --muted: #5f6b7a;
  --line: #dfe5ee;
  --soft: #f6f8fb;
  --blue: #1f5eff;
  --green: #0f8a5f;
  --orange: #b76600;
  --red: #b42318;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 32px 18px 56px;
  background: #eef2f7;
  color: var(--fg);
  font: 16px/1.78 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
}
main {
  max-width: 1120px;
  margin: 0 auto;
  background: white;
  border: 1px solid var(--line);
  border-radius: 18px;
  box-shadow: 0 18px 50px rgba(21, 31, 50, .10);
  overflow: hidden;
}
.hero {
  padding: 34px 42px 28px;
  background: linear-gradient(135deg, #102044, #244bd6);
  color: white;
}
.hero h1 {
  margin: 0 0 10px;
  font-size: 30px;
  line-height: 1.25;
}
.hero p {
  margin: 0;
  opacity: .88;
}
.content {
  padding: 28px 42px 42px;
}
h2 {
  margin: 34px 0 14px;
  padding-top: 8px;
  border-top: 1px solid var(--line);
  font-size: 23px;
}
h3 {
  margin: 26px 0 10px;
  font-size: 18px;
}
p { margin: 10px 0; }
blockquote {
  margin: 16px 0;
  padding: 12px 16px;
  border-left: 4px solid var(--blue);
  background: #f2f6ff;
  border-radius: 8px;
}
code {
  padding: 2px 5px;
  border-radius: 5px;
  background: #f1f4f8;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: .92em;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0 20px;
  font-size: 14px;
}
th, td {
  border: 1px solid var(--line);
  padding: 9px 11px;
  vertical-align: top;
}
th {
  background: #f3f6fa;
  text-align: left;
  font-weight: 700;
}
tr:nth-child(even) td { background: #fbfcfe; }
ul, ol { padding-left: 24px; }
li { margin: 5px 0; }
.badge {
  display: inline-block;
  margin: 0 8px 8px 0;
  padding: 4px 10px;
  border-radius: 999px;
  background: #eef4ff;
  color: #2145a8;
  font-size: 13px;
  font-weight: 650;
}
.note {
  margin: 18px 0;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid #f0d6a3;
  background: #fff8eb;
}
@media (max-width: 760px) {
  body { padding: 12px; }
  .hero, .content { padding-left: 20px; padding-right: 20px; }
  table { display: block; overflow-x: auto; }
}
"""


def inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def table_to_html(lines: list[str]) -> str:
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c) <= {"-", ":", " "} for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return ""
    out = ["<table>"]
    for idx, row in enumerate(rows):
        tag = "th" if idx == 0 else "td"
        out.append("<tr>" + "".join(f"<{tag}>{inline_markdown(c)}</{tag}>" for c in row) + "</tr>")
    out.append("</table>")
    return "\n".join(out)


def markdown_to_html(markdown: str) -> tuple[str, str]:
    title = "DrawingPT 第一周复现与调研报告"
    body: list[str] = []
    paragraph: list[str] = []
    list_mode: str | None = None
    table: list[str] = []
    quote: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            body.append("<p>" + inline_markdown(" ".join(paragraph)) + "</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_mode
        if list_mode:
            body.append(f"</{list_mode}>")
            list_mode = None

    def flush_table() -> None:
        nonlocal table
        if table:
            body.append(table_to_html(table))
            table = []

    def flush_quote() -> None:
        nonlocal quote
        if quote:
            body.append("<blockquote>" + "\n".join(f"<p>{inline_markdown(q)}</p>" for q in quote) + "</blockquote>")
            quote = []

    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("|") and line.endswith("|"):
            flush_paragraph()
            flush_list()
            flush_quote()
            table.append(line)
            continue
        flush_table()

        if not line.strip():
            flush_paragraph()
            flush_list()
            flush_quote()
            continue
        if line.startswith("# "):
            flush_paragraph()
            flush_list()
            flush_quote()
            title = line[2:].strip()
            continue
        if line.startswith("## "):
            flush_paragraph()
            flush_list()
            flush_quote()
            body.append(f"<h2>{inline_markdown(line[3:].strip())}</h2>")
            continue
        if line.startswith("### "):
            flush_paragraph()
            flush_list()
            flush_quote()
            body.append(f"<h3>{inline_markdown(line[4:].strip())}</h3>")
            continue
        if line.startswith("> "):
            flush_paragraph()
            flush_list()
            quote.append(line[2:].strip())
            continue
        m = re.match(r"^(\d+)\.\s+(.*)$", line)
        if m:
            flush_paragraph()
            flush_quote()
            if list_mode != "ol":
                flush_list()
                body.append("<ol>")
                list_mode = "ol"
            body.append(f"<li>{inline_markdown(m.group(2))}</li>")
            continue
        if line.startswith("- "):
            flush_paragraph()
            flush_quote()
            if list_mode != "ul":
                flush_list()
                body.append("<ul>")
                list_mode = "ul"
            body.append(f"<li>{inline_markdown(line[2:].strip())}</li>")
            continue
        flush_list()
        flush_quote()
        paragraph.append(line.strip())

    flush_paragraph()
    flush_list()
    flush_table()
    flush_quote()
    return title, "\n".join(body)


def main() -> None:
    markdown = SOURCE.read_text(encoding="utf-8")
    title, content = markdown_to_html(markdown)
    html_doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{CSS}</style>
</head>
<body>
  <main>
    <section class="hero">
      <span class="badge">DrawingPT</span>
      <span class="badge">第一周复现</span>
      <span class="badge">中文可读版</span>
      <h1>{html.escape(title)}</h1>
      <p>把机器产物、Slurm 日志、baseline 数字和文献调研整理成组会上能直接讲的版本。</p>
    </section>
    <section class="content">
      {content}
    </section>
  </main>
</body>
</html>
"""
    TARGET.write_text(html_doc, encoding="utf-8")


if __name__ == "__main__":
    main()
