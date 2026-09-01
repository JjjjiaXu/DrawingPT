from __future__ import annotations

import html
from pathlib import Path

from build_engineering_cost_report import CSS, markdown_to_html


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "next_steps_2026-09-01"
SOURCE = REPORT_DIR / "report_readable_cn.md"
TARGET = REPORT_DIR / "report.html"


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
      <span class="badge">下一阶段</span>
      <span class="badge">三件事推进</span>
      <span class="badge">训练闭环 smoke</span>
      <h1>{html.escape(title)}</h1>
      <p>把 CADTransformer 评估门禁、DrawingPT v0 prereg、FloorPlanCAD 工程量 proxy 和最小 masked primitive 训练闭环收束成下次组会可讲的材料。</p>
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
