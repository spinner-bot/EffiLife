#!/usr/bin/env python3
"""Render the design review as one offline HTML file.

Usage: python3 scripts/build_design_review.py
Build dependency: Python-Markdown (python3 -m pip install Markdown).
"""

from html import escape
from pathlib import Path
import re

try:
    import markdown
except ImportError as error:
    raise SystemExit("Install the renderer with: python3 -m pip install Markdown") from error


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = (
    ("product", "产品设计", "11-user-design.md"),
    ("architecture", "系统架构", "13-system-architecture.md"),
    ("roadmap", "远期目标", "12-long-term-goals.md"),
)
OUTPUT = ROOT / "refactor" / "design-review.html"

STYLE = """
:root {
  color-scheme: light;
  --page: #f5f6f8; --paper: #ffffff; --ink: #182330;
  --muted: #526071; --line: #dce2e9; --accent: #274ab0;
  --confirmed: #126647; --confirmed-bg: #f0f8f4;
  --proposal: #795019; --proposal-bg: #fff8ed;
  --radius: 12px;
}
* { box-sizing: border-box; }
html { scroll-padding-top: 24px; }
body {
  margin: 0; background: var(--page); color: var(--ink);
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", "Microsoft YaHei", sans-serif;
  font-size: 16px; line-height: 1.9; overflow-wrap: anywhere;
}
a { color: var(--accent); text-underline-offset: 4px; }
a:hover { text-decoration-thickness: 2px; }
a:focus-visible, button:focus-visible, summary:focus-visible, [tabindex]:focus-visible {
  outline: 3px solid var(--accent); outline-offset: 4px;
}
.skip { position: absolute; left: 16px; top: -100px; padding: 10px 18px; background: var(--paper); z-index: 5; }
.skip:focus { top: 12px; }
.layout { display: grid; grid-template-columns: 272px minmax(0, 1fr); max-width: 1450px; margin: auto; }
.sidebar {
  position: sticky; top: 0; height: 100vh; overflow-y: auto;
  padding: 30px 22px 36px; border-right: 1px solid var(--line);
}
.brand { margin: 0; font-size: 19px; font-weight: 750; letter-spacing: -.4px; }
.sidebar-label { margin: 0 0 24px; font-size: 14px; color: var(--muted); }
.sidebar details { padding: 12px 0; border-top: 1px solid var(--line); }
.sidebar summary { cursor: pointer; font-weight: 650; padding: 3px 0; }
.sidebar .toc { font-size: 14px; line-height: 1.65; }
.sidebar ul { list-style: none; padding: 0; margin: 10px 0 0; }
.sidebar ul ul { padding-left: 14px; margin-top: 5px; }
.sidebar li { margin: 8px 0; }
.sidebar a { display: inline-block; color: var(--muted); text-decoration: none; }
.sidebar a:hover { color: var(--accent); text-decoration: underline; }
.sidebar-note { font-size: 13px; color: var(--muted); margin-top: 24px; }
main { min-width: 0; padding: 46px clamp(22px, 4vw, 64px) 80px; }
.eyebrow { margin: 0 0 10px; color: var(--accent); font-size: 13px; font-weight: 700; letter-spacing: 1.4px; }
h1 { margin: 0; font-size: clamp(28px, 3vw, 40px); line-height: 1.35; letter-spacing: -.8px; }
.intro { color: var(--muted); max-width: 44em; margin: 16px 0 20px; }
.meta { display: flex; gap: 10px 20px; flex-wrap: wrap; color: var(--muted); font-size: 14px; }
.toolbar { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; margin-top: 22px; }
button {
  font: inherit; font-size: 14px; color: var(--ink); background: var(--paper);
  border: 1px solid var(--line); padding: 9px 16px; border-radius: 8px; cursor: pointer;
}
button:hover { border-color: var(--accent); color: var(--accent); }
.legend { display: flex; flex-wrap: wrap; gap: 10px 18px; padding: 18px 0; margin: 24px 0; border-block: 1px solid var(--line); font-size: 14px; }
.legend span { display: inline-flex; gap: 8px; align-items: center; }
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; background: var(--confirmed); }
.dot.proposal { background: var(--proposal); }
.dot.direction { background: var(--accent); }
.document { background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius); padding: clamp(22px, 3vw, 40px); margin-top: 28px; }
.document-top { display: flex; justify-content: space-between; gap: 16px; color: var(--muted); font-size: 13px; margin-bottom: 14px; }
.document-top a { color: var(--muted); }
h2, h3, h4, h5 { line-height: 1.5; scroll-margin-top: 24px; }
h2 { font-size: 26px; margin: 0 0 24px; }
h3 { font-size: 21px; margin: 40px 0 16px; border-top: 1px solid var(--line); padding-top: 24px; }
h4 { font-size: 17px; margin: 26px 0 12px; }
p { margin: 14px 0; }
ul, ol { padding-left: 1.55em; }
li { margin: 7px 0; }
li > p { margin: 6px 0; }
strong { font-weight: 680; }
code { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: .9em; background: #edf0f5; padding: 2px 5px; border-radius: 4px; }
pre { overflow-x: auto; padding: 16px; border: 1px solid var(--line); border-radius: 8px; }
pre code { padding: 0; background: transparent; }
.requirement { border-left: 3px solid var(--confirmed); padding: 16px 18px; background: var(--confirmed-bg); border-radius: 0 8px 8px 0; }
.requirement.proposal { border-color: var(--proposal); background: var(--proposal-bg); }
.requirement.direction { border-color: var(--accent); background: #f1f5ff; }
.status { display: block; font-size: 12px; font-weight: 650; color: var(--confirmed); margin-bottom: 6px; }
.proposal .status { color: var(--proposal); }
.direction .status { color: var(--accent); }
.permalink { display: inline-block; margin-left: 7px; font-weight: 400; font-size: 13px; text-decoration: none; }
.requirement:target { outline: 2px solid var(--accent); outline-offset: 4px; }
.table-scroll { width: 100%; overflow-x: auto; margin: 18px 0; border: 1px solid var(--line); border-radius: 8px; }
table { border-collapse: collapse; width: 100%; min-width: 540px; text-align: left; font-size: 14px; line-height: 1.8; }
th, td { padding: 12px 14px; vertical-align: top; border-bottom: 1px solid var(--line); }
th { background: #f4f6fa; font-weight: 650; }
tr:last-child td { border-bottom: 0; }
th:first-child, td:first-child { min-width: 110px; }
blockquote { padding-left: 18px; border-left: 3px solid var(--line); color: var(--muted); margin-inline: 0; }
footer { padding-top: 28px; font-size: 13px; color: var(--muted); }
@media (max-width: 900px) {
  .layout { display: block; }
  .sidebar { position: static; height: auto; padding: 20px 22px; border-right: 0; border-bottom: 1px solid var(--line); }
  .sidebar-label { margin-bottom: 10px; }
  .sidebar-note { margin: 10px 0 0; }
  main { padding-top: 28px; }
  .document { padding: 22px 18px; }
}
@media (max-width: 480px) {
  body { font-size: 15px; }
  main { padding-inline: 14px; }
  .requirement { padding: 14px; }
  h2 { font-size: 23px; }
  h3 { font-size: 19px; }
}
@media print {
  :root { --page: #fff; --line: #bbb; }
  body { font-size: 11pt; line-height: 1.7; }
  .layout { display: block; max-width: none; }
  .sidebar, .toolbar, .skip, .permalink, .document-top { display: none; }
  main { padding: 0; }
  h1 { font-size: 25pt; }
  h2 { font-size: 20pt; }
  h3 { font-size: 15pt; }
  h2, h3, h4 { break-after: avoid; }
  .document { border: 0; border-radius: 0; padding: 0; margin-top: 28px; }
  .document + .document { break-before: page; }
  .requirement { break-inside: avoid; background: transparent !important; }
  .table-scroll { overflow: visible; border-radius: 0; }
  table { min-width: 0; font-size: 10pt; }
  tr { break-inside: avoid; }
  a { color: inherit; }
}
"""


def render_document(document_id, label, filename):
    def slugify(value, separator):
        slug = re.sub(r"[^\w\u4e00-\u9fff]+", separator, value).strip(separator)
        return f"{document_id}-{slug.lower()}"

    renderer = markdown.Markdown(
        extensions=["extra", "toc", "sane_lists"],
        extension_configs={"toc": {"baselevel": 2, "toc_depth": "2-3", "slugify": slugify}},
    )
    source = ROOT / "refactor" / filename
    content = renderer.convert(source.read_text(encoding="utf-8"))

    def decorate_requirement(match):
        kind, number, heading = match.groups()
        key = f"{kind}-{number}"
        style, status = ("confirmed", "用户已明确") if kind == "R" else ("proposal", "Codex 提案 · 待审计")
        if key == "R-010":
            style, status = "direction", "用户探索方向 · 具体规则待细化"
        return (
            f'<p class="requirement {style}" id="{key.lower()}">'
            f'<span class="status">{status}</span><strong>{key} {heading}</strong>'
            f'<a class="permalink" href="#{key.lower()}" aria-label="定位 {key}">#</a>'
        )

    content = re.sub(r"<p><strong>(R|P)-(\d{3}) (.*?)</strong>", decorate_requirement, content)
    content = content.replace("<th>", '<th scope="col">')
    table_number = 0

    def wrap_table(match):
        nonlocal table_number
        table_number += 1
        return (
            f'<div class="table-scroll" role="region" tabindex="0" '
            f'aria-label="{escape(label)}：表格 {table_number}">{match.group(0)}</div>'
        )

    content = re.sub(r"<table>.*?</table>", wrap_table, content, flags=re.DOTALL)
    for target_id, _, target_file in DOCUMENTS:
        content = content.replace(f'href="{target_file}"', f'href="#{target_id}"')

    article = (
        f'<article class="document" id="{document_id}" aria-label="{escape(label)}">'
        f'<div class="document-top"><span>{escape(label)}</span>'
        f'<a href="{filename}">Markdown 源文档</a></div>{content}</article>'
    )
    navigation = (
        f'<details open><summary>{escape(label)}</summary>'
        f'{renderer.toc}</details>'
    )
    return article, navigation


def main():
    articles, navigation = [], []
    for document in DOCUMENTS:
        article, toc = render_document(*document)
        articles.append(article)
        navigation.append(toc)

    page = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="author" content="Codex  (sqs_A100)">
  <meta name="description" content="EffiLife 产品设计、系统架构与远期目标审阅稿。">
  <title>EffiLife · 产品设计审阅稿</title>
  <style>__STYLE__</style>
</head>
<body>
<a class="skip" href="#content">跳到文档正文</a>
<div class="layout">
  <aside class="sidebar" aria-label="文档目录">
    <p class="brand">EffiLife</p>
    <p class="sidebar-label">设计文档 · 审阅版</p>
    <nav aria-label="章节导航">__NAVIGATION__</nav>
    <p class="sidebar-note">可按 R / P 编号提出修改意见。章节与条目支持直接链接。</p>
  </aside>
  <main id="content" tabindex="-1">
    <header>
      <p class="eyebrow">EFFILIFE / DESIGN REVIEW</p>
      <h1>个人生活管理的产品设计</h1>
      <p class="intro">以时间与事件两条主线关联个人生活，整理统一录入、信息层级、使用动线与可扩展系统架构。下文完整收录三份设计文档，供逐条审计与修改。</p>
      <div class="meta"><span>2026-11-10</span><span>产品稿 v0.2</span><span>作者：Codex  (sqs_A100)</span><span>状态：待审计</span></div>
      <div class="toolbar"><button type="button" id="print-button" hidden>打印 / 导出 PDF</button><a href="#product">开始阅读</a><a href="#architecture">系统架构</a><a href="#roadmap">远期目标</a></div>
    </header>
    <div class="legend" aria-label="条目状态说明">
      <span><i class="dot" aria-hidden="true"></i>用户已明确的要求</span>
      <span><i class="dot direction" aria-hidden="true"></i>用户探索方向</span>
      <span><i class="dot proposal" aria-hidden="true"></i>Codex 提案，待审计</span>
    </div>
    __ARTICLES__
    <footer>本页从 Markdown 源文档生成，支持离线阅读。源文档链接适用于仓库内阅读；文内三份文档之间可直接跳转。</footer>
  </main>
</div>
<script>
  const printButton = document.getElementById('print-button');
  printButton.hidden = false;
  printButton.addEventListener('click', () => window.print());
</script>
</body>
</html>
"""
    page = page.replace("__STYLE__", STYLE)
    page = page.replace("__NAVIGATION__", "\n".join(navigation))
    page = page.replace("__ARTICLES__", "\n".join(articles))
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"Generated {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
