from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "engineering_cost_research_2026-08-23"
SOURCE = REPORT_DIR / "report_readable_cn.md"
TARGET = REPORT_DIR / "report.html"


CSS = """
:root {
  color-scheme: light;
  --fg: #142033;
  --muted: #607086;
  --line: #dfe6f0;
  --soft: #f5f8fc;
  --blue: #1f5eff;
  --cyan: #007f9f;
  --green: #0e8a62;
  --orange: #b76700;
  --red: #b42318;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 30px 18px 56px;
  background:
    radial-gradient(circle at top left, rgba(31, 94, 255, .13), transparent 32rem),
    linear-gradient(180deg, #eef3f9, #e8eef7);
  color: var(--fg);
  font: 16px/1.78 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
}
main {
  max-width: 1160px;
  margin: 0 auto;
  background: white;
  border: 1px solid var(--line);
  border-radius: 20px;
  box-shadow: 0 20px 55px rgba(20, 32, 51, .12);
  overflow: hidden;
}
.hero {
  padding: 34px 42px 28px;
  background:
    linear-gradient(135deg, rgba(12, 25, 58, .96), rgba(24, 80, 204, .92)),
    radial-gradient(circle at 82% 18%, rgba(255, 255, 255, .25), transparent 15rem);
  color: white;
}
.hero h1 {
  margin: 0 0 10px;
  font-size: 31px;
  line-height: 1.24;
  letter-spacing: .01em;
}
.hero p {
  max-width: 780px;
  margin: 0;
  opacity: .88;
}
.badge {
  display: inline-block;
  margin: 0 8px 12px 0;
  padding: 4px 11px;
  border-radius: 999px;
  background: rgba(255, 255, 255, .14);
  color: white;
  border: 1px solid rgba(255, 255, 255, .22);
  font-size: 13px;
  font-weight: 700;
}
.content {
  padding: 28px 42px 44px;
}
h2 {
  margin: 34px 0 14px;
  padding-top: 9px;
  border-top: 1px solid var(--line);
  font-size: 23px;
}
h3 {
  margin: 26px 0 10px;
  font-size: 18px;
}
p { margin: 10px 0; }
a {
  color: #1e55d6;
  text-decoration: none;
  border-bottom: 1px solid rgba(30, 85, 214, .28);
}
a:hover { border-bottom-color: currentColor; }
blockquote {
  margin: 16px 0;
  padding: 12px 16px;
  border-left: 4px solid var(--blue);
  background: #f2f6ff;
  border-radius: 10px;
}
code {
  padding: 2px 5px;
  border-radius: 5px;
  background: #f0f4f8;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: .92em;
}
pre {
  margin: 14px 0 20px;
  padding: 14px 16px;
  overflow-x: auto;
  border: 1px solid #d9e3ef;
  border-radius: 12px;
  background: #0f1a2a;
  color: #e8eef7;
  font: 14px/1.65 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
pre code {
  padding: 0;
  background: transparent;
  color: inherit;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0 22px;
  font-size: 14px;
}
th, td {
  border: 1px solid var(--line);
  padding: 9px 11px;
  vertical-align: top;
}
th {
  background: #f2f6fb;
  text-align: left;
  font-weight: 750;
}
tr:nth-child(even) td { background: #fbfcfe; }
ul, ol { padding-left: 24px; }
li { margin: 5px 0; }
.lead-card {
  margin: 8px 0 24px;
  padding: 16px 18px;
  border: 1px solid #bfdbfe;
  background: linear-gradient(180deg, #eff6ff, #f8fbff);
  border-radius: 14px;
}
.lead-card p {
  margin: 6px 0;
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

    def link(match: re.Match[str]) -> str:
        label = match.group(1)
        url = match.group(2)
        return f'<a href="{url}" target="_blank" rel="noreferrer">{label}</a>'

    escaped = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", link, escaped)
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
    title = "工程造价自动估算调研汇报"
    body: list[str] = []
    paragraph: list[str] = []
    list_mode: str | None = None
    table: list[str] = []
    quote: list[str] = []
    code_block: list[str] | None = None

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(paragraph)
            css_class = ' class="lead-card"' if text.startswith("工程造价自动估算已经有") else ""
            body.append(f"<div{css_class}><p>{inline_markdown(text)}</p></div>" if css_class else f"<p>{inline_markdown(text)}</p>")
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

    def flush_code_block() -> None:
        nonlocal code_block
        if code_block is not None:
            code = html.escape("\n".join(code_block))
            body.append(f"<pre><code>{code}</code></pre>")
            code_block = None

    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if code_block is None:
                flush_paragraph()
                flush_list()
                flush_table()
                flush_quote()
                code_block = []
            else:
                flush_code_block()
            continue
        if code_block is not None:
            code_block.append(line)
            continue
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
        ordered = re.match(r"^(\d+)\.\s+(.*)$", line)
        if ordered:
            flush_paragraph()
            flush_quote()
            if list_mode != "ol":
                flush_list()
                body.append("<ol>")
                list_mode = "ol"
            body.append(f"<li>{inline_markdown(ordered.group(2))}</li>")
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
    flush_code_block()
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
      <span class="badge">工程造价</span>
      <span class="badge">文献调研</span>
      <h1>{html.escape(title)}</h1>
      <p>围绕“2D CAD / 施工图能否端到端输出工程造价”整理研究现状、可行链路和 DrawingPT 的切入点。</p>
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
