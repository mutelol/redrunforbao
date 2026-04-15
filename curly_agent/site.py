from __future__ import annotations

import html
import json
import os
import re
import shutil
from pathlib import Path

from .utils import ensure_dir

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".svg"}


def build_static_site(project_root: Path, runs_root: Path, site_root: Path) -> Path:
    del project_root
    ensure_dir(site_root)
    _reset_site_output(site_root)
    records = _collect_run_records(runs_root, site_root)

    (site_root / "data.json").write_text(
        json.dumps(
            {
                "generated_count": len(records),
                "items": records,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (site_root / "index.html").write_text(_index_html(), encoding="utf-8")
    (site_root / "styles.css").write_text(_styles_css(), encoding="utf-8")
    (site_root / "app.js").write_text(_app_js(), encoding="utf-8")
    (site_root / ".nojekyll").write_text("", encoding="utf-8")

    items_root = ensure_dir(site_root / "items")
    for record in records:
        detail_path = items_root / f"{record['run_name']}.html"
        detail_path.write_text(_detail_html(site_root, detail_path, record), encoding="utf-8")

    return site_root / "index.html"


def _reset_site_output(site_root: Path) -> None:
    for name in ("records", "items"):
        target = site_root / name
        if target.exists():
            shutil.rmtree(target)


def _collect_run_records(runs_root: Path, site_root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    if not runs_root.exists():
        return records

    records_root = ensure_dir(site_root / "records")
    for metadata_path in sorted(runs_root.glob("*/metadata.json"), reverse=True):
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        run_dir = metadata_path.parent
        record_root = ensure_dir(records_root / run_dir.name)
        copied_assets = _copy_record_bundle(run_dir, record_root, site_root)

        selected = payload.get("selected_item") or {}
        content_pack = payload.get("content_pack") or {}
        cover = content_pack.get("cover") or {}
        image_plan = content_pack.get("image_plan") or {}
        post_draft = content_pack.get("post_draft") or {}
        markdown_text = copied_assets["content_markdown"]

        records.append(
            {
                "run_name": run_dir.name,
                "generated_at": payload.get("generated_at", ""),
                "content_type": selected.get("content_type", ""),
                "title": selected.get("title", ""),
                "source_url": selected.get("url", ""),
                "price_text": selected.get("price_text", ""),
                "summary": content_pack.get("summary", ""),
                "hook": (content_pack.get("hooks") or [""])[0],
                "title_option": (content_pack.get("titles") or [""])[0],
                "opening": post_draft.get("opening", ""),
                "body": post_draft.get("body", ""),
                "closing": post_draft.get("closing", ""),
                "tags": content_pack.get("tags", []),
                "cover_main": cover.get("main_cover_line", ""),
                "cover_secondary": cover.get("secondary_cover_line", ""),
                "cover_design": image_plan.get("cover_design", {}),
                "cover_url": copied_assets["cover_url"],
                "gallery_urls": copied_assets["gallery_urls"],
                "content_markdown": markdown_text,
                "content_markdown_url": copied_assets["content_markdown_url"],
                "detail_url": f"./items/{run_dir.name}.html",
            }
        )
    return records


def _copy_record_bundle(run_dir: Path, record_root: Path, site_root: Path) -> dict[str, object]:
    assets_root = ensure_dir(record_root / "assets")
    source_assets = run_dir / "assets"
    copied_asset_paths: list[Path] = []

    if source_assets.exists():
        for asset_path in sorted(source_assets.iterdir()):
            if asset_path.is_file():
                target = assets_root / asset_path.name
                shutil.copy2(asset_path, target)
                copied_asset_paths.append(target)

    content_markdown = ""
    content_source = run_dir / "content-pack.md"
    content_target = record_root / "content-pack.md"
    if content_source.exists():
        shutil.copy2(content_source, content_target)
        content_markdown = content_target.read_text(encoding="utf-8")

    ordered_gallery = _ordered_gallery_paths(copied_asset_paths)
    return {
        "cover_url": _site_rel(site_root, ordered_gallery[0]) if ordered_gallery else "",
        "gallery_urls": [_site_rel(site_root, path) for path in ordered_gallery],
        "content_markdown": content_markdown,
        "content_markdown_url": _site_rel(site_root, content_target) if content_target.exists() else "",
    }


def _ordered_gallery_paths(paths: list[Path]) -> list[Path]:
    visible = [path for path in paths if path.suffix.lower() in IMAGE_SUFFIXES]

    def sort_key(path: Path) -> tuple[int, str]:
        name = path.name.lower()
        if name == "cover.svg":
            return (0, name)
        if name.startswith("primary."):
            return (1, name)
        if name.startswith("detail-"):
            return (2, name)
        return (3, name)

    return sorted(visible, key=sort_key)


def _site_rel(site_root: Path, path: Path) -> str:
    return path.resolve().relative_to(site_root.resolve()).as_posix()


def _detail_html(site_root: Path, detail_path: Path, record: dict[str, object]) -> str:
    gallery_urls = record.get("gallery_urls") or []
    gallery_html = _gallery_html(site_root, detail_path, gallery_urls)
    tags_html = "".join(
        f'<span class="tag">#{html.escape(str(tag))}</span>'
        for tag in (record.get("tags") or [])
    )
    content_html = _render_markdown(str(record.get("content_markdown") or ""))
    back_href = html.escape(_from_page(detail_path, site_root / "index.html"))
    source_href = html.escape(str(record.get("source_url") or ""))
    cover_design = record.get("cover_design") or {}
    cover_note = ""
    if cover_design:
        cover_note = (
            f'<p class="detail-meta-row"><strong>封面风格</strong>'
            f'{html.escape(str(cover_design.get("template") or ""))}'
            f' / {html.escape(str(cover_design.get("palette") or ""))}</p>'
        )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{html.escape(str(record.get("title_option") or record.get("title") or "Curly 内容"))}</title>
  <link rel="stylesheet" href="{back_href.replace('index.html', 'styles.css')}">
</head>
<body class="detail-page">
  <main class="detail-shell">
    <a class="back-link" href="{back_href}">返回库存页</a>
    <header class="detail-hero">
      <div class="detail-copy">
        <p class="eyebrow">Curly Collection</p>
        <h1>{html.escape(str(record.get("title_option") or record.get("title") or ""))}</h1>
        <p class="detail-lead">{html.escape(str(record.get("opening") or record.get("summary") or ""))}</p>
        <div class="tag-list">{tags_html}</div>
        <div class="detail-meta">
          <p class="detail-meta-row"><strong>栏目</strong>{html.escape(str(record.get("content_type") or "内容库存"))}</p>
          <p class="detail-meta-row"><strong>生成时间</strong>{html.escape(str(record.get("generated_at") or ""))}</p>
          {f'<p class="detail-meta-row"><strong>参考价格</strong>{html.escape(str(record.get("price_text") or ""))}</p>' if record.get("price_text") else ''}
          {cover_note}
        </div>
        {f'<a class="source-link" href="{source_href}" target="_blank" rel="noreferrer">查看官网原链接</a>' if source_href else ''}
      </div>
    </header>

    <section class="detail-section">
      <div class="section-title-row">
        <h2>图片素材</h2>
        <p>这里展示当前记录里同步出来的 assets，手机上直接翻就行。</p>
      </div>
      <div class="detail-gallery">
        {gallery_html or '<div class="empty-state">这条记录没有同步到图片素材。</div>'}
      </div>
    </section>

    <section class="detail-section">
      <div class="section-title-row">
        <h2>内容包</h2>
        <p>下面是这条记录的 content-pack，已经转成更适合阅读的页面。</p>
      </div>
      <article class="markdown-body">
        {content_html or '<p>这条记录没有找到 content-pack 文本。</p>'}
      </article>
    </section>
  </main>
</body>
</html>
"""


def _from_page(page_path: Path, target_path: Path) -> str:
    return Path(os.path.relpath(target_path, start=page_path.parent)).as_posix()


def _gallery_html(site_root: Path, detail_path: Path, gallery_urls: object) -> str:
    if not isinstance(gallery_urls, list):
        return ""

    cards: list[str] = []
    for index, path in enumerate(gallery_urls, start=1):
        image_path = site_root / str(path)
        image_href = html.escape(_from_page(detail_path, image_path))
        image_name = html.escape(_download_name(index, image_path))
        cards.append(
            f"""
            <figure class="image-card">
              <a class="image-open-link" href="{image_href}" target="_blank" rel="noreferrer">
                <img class="detail-image" src="{image_href}" alt="图片素材 {index}">
              </a>
              <figcaption class="image-caption">
                <span>图片 {index}</span>
                <span class="image-actions">
                  <a href="{image_href}" target="_blank" rel="noreferrer">打开原图</a>
                  <a href="{image_href}" download="{image_name}">下载图片</a>
                </span>
              </figcaption>
            </figure>
            """
        )
    return "".join(cards)


def _download_name(index: int, image_path: Path) -> str:
    suffix = image_path.suffix or ".jpg"
    if image_path.name.lower() == "cover.svg":
        return f"curly-cover-{index}{suffix}"
    return f"curly-image-{index}{suffix}"


def _render_markdown(markdown_text: str) -> str:
    lines = markdown_text.replace("\r\n", "\n").split("\n")
    html_parts: list[str] = []
    paragraph_lines: list[str] = []
    list_items: list[str] = []
    in_code = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            text = " ".join(line.strip() for line in paragraph_lines if line.strip())
            html_parts.append(f"<p>{_inline_markdown(text)}</p>")
            paragraph_lines.clear()

    def flush_list() -> None:
        if list_items:
            html_parts.append("<ul>" + "".join(f"<li>{_inline_markdown(item)}</li>" for item in list_items) + "</ul>")
            list_items.clear()

    def flush_code() -> None:
        if code_lines:
            html_parts.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
            code_lines.clear()

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        if stripped.startswith("### "):
            flush_paragraph()
            flush_list()
            html_parts.append(f"<h3>{_inline_markdown(stripped[4:])}</h3>")
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            flush_list()
            html_parts.append(f"<h2>{_inline_markdown(stripped[3:])}</h2>")
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            flush_list()
            html_parts.append(f"<h1>{_inline_markdown(stripped[2:])}</h1>")
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            list_items.append(stripped[2:])
            continue

        paragraph_lines.append(stripped)

    flush_paragraph()
    flush_list()
    flush_code()
    return "".join(html_parts)


def _inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(
        r"(https?://[^\s<]+)",
        lambda match: f'<a href="{match.group(1)}" target="_blank" rel="noreferrer">{match.group(1)}</a>',
        escaped,
    )
    return escaped


def _index_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Curly Collection 内容库存</title>
  <link rel="stylesheet" href="./styles.css">
</head>
<body>
  <main class="app-shell">
    <header class="hero">
      <div>
        <p class="eyebrow">Curly Collection</p>
        <h1>内容库存页</h1>
        <p class="hero-copy">这里专门给你和你老婆挑题、看图、看正文。每次本地 run 完以后，新的内容会被整理进这个静态页面里，后面直接发到 GitHub Pages 就能随时随地打开。</p>
      </div>
      <div class="hero-meta">
        <div class="meta-card">
          <span class="meta-label">当前库存</span>
          <strong id="itemCount">加载中</strong>
          <span class="meta-footnote">展示图片素材 + content-pack 正文</span>
        </div>
      </div>
    </header>

    <section class="toolbar">
      <input id="searchInput" class="search-input" type="search" placeholder="搜标题、正文关键词、标签">
      <div class="filter-row">
        <button class="filter-chip is-active" data-filter="all">全部</button>
        <button class="filter-chip" data-filter="新品速递">新品速递</button>
        <button class="filter-chip" data-filter="旧款回看">旧款回看</button>
      </div>
    </section>

    <section id="cards" class="cards"></section>
  </main>
  <script src="./app.js"></script>
</body>
</html>
"""


def _styles_css() -> str:
    return """:root {
  --bg: #fbf6f1;
  --surface: rgba(255,255,255,0.88);
  --surface-strong: #fffdfa;
  --text: #352821;
  --muted: #76695f;
  --line: rgba(88, 60, 44, 0.11);
  --accent: #d97b92;
  --accent-strong: #b95772;
  --accent-soft: #f7dbe3;
  --accent-warm: #f5e6d5;
  --shadow: 0 18px 48px rgba(78, 49, 34, 0.10);
}

* { box-sizing: border-box; }

body {
  margin: 0;
  color: var(--text);
  font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
  background:
    radial-gradient(circle at top left, #fff2f6 0, transparent 30%),
    radial-gradient(circle at top right, #fff8ea 0, transparent 28%),
    linear-gradient(180deg, #fcf8f4 0%, #f7efe8 100%);
}

a { color: inherit; }

.app-shell,
.detail-shell {
  max-width: 1180px;
  margin: 0 auto;
  padding: 28px 18px 72px;
}

.hero,
.toolbar,
.card,
.detail-hero,
.detail-section {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 28px;
  box-shadow: var(--shadow);
  backdrop-filter: blur(18px);
}

.hero {
  display: grid;
  grid-template-columns: 1.5fr 0.8fr;
  gap: 18px;
  padding: 28px;
  align-items: stretch;
}

.eyebrow {
  margin: 0 0 10px;
  color: var(--accent-strong);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  font-size: clamp(28px, 6vw, 54px);
  line-height: 1.02;
}

.hero-copy,
.detail-lead {
  margin: 14px 0 0;
  color: var(--muted);
  font-size: 16px;
  line-height: 1.75;
}

.hero-meta {
  display: flex;
  align-items: end;
  justify-content: stretch;
}

.meta-card {
  width: 100%;
  min-height: 150px;
  padding: 22px;
  border-radius: 24px;
  background: linear-gradient(180deg, #fffefb 0%, #f7efe7 100%);
  border: 1px solid var(--line);
}

.meta-label,
.meta-footnote {
  display: block;
  color: var(--muted);
  font-size: 13px;
}

.meta-card strong {
  display: block;
  margin-top: 12px;
  font-size: 36px;
}

.meta-footnote {
  margin-top: 10px;
  line-height: 1.6;
}

.toolbar {
  margin-top: 18px;
  padding: 18px;
}

.search-input {
  width: 100%;
  border: 1px solid var(--line);
  background: #fffdfa;
  border-radius: 18px;
  padding: 14px 16px;
  font-size: 16px;
  color: var(--text);
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.filter-chip {
  border: 0;
  border-radius: 999px;
  padding: 10px 16px;
  background: #f4e7df;
  color: var(--text);
  cursor: pointer;
  font-size: 14px;
}

.filter-chip.is-active {
  background: var(--accent);
  color: white;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 18px;
  margin-top: 18px;
}

.card {
  overflow: hidden;
}

.card-cover {
  display: block;
  width: 100%;
  aspect-ratio: 4 / 5;
  object-fit: cover;
  background: linear-gradient(180deg, #f7dbe3 0%, #f7efe2 100%);
}

.card-body {
  padding: 18px;
}

.card-type {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  background: #f9ede7;
  color: var(--accent-strong);
  font-size: 12px;
  font-weight: 700;
}

.card-title {
  margin: 14px 0 0;
  font-size: 22px;
  line-height: 1.4;
}

.card-copy {
  margin: 12px 0 0;
  color: var(--muted);
  line-height: 1.75;
  font-size: 14px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.tag {
  padding: 7px 10px;
  border-radius: 999px;
  background: #fff4ee;
  color: #7f6150;
  font-size: 12px;
}

.meta-list {
  margin-top: 14px;
  font-size: 13px;
  color: var(--muted);
  line-height: 1.7;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.action-link,
.source-link,
.back-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  border-radius: 14px;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 700;
}

.action-link,
.source-link {
  background: var(--accent);
  color: white;
}

.action-link.secondary,
.back-link {
  background: #efe3da;
  color: var(--text);
}

.empty-state {
  padding: 22px;
  border-radius: 18px;
  background: var(--surface-strong);
  color: var(--muted);
  line-height: 1.7;
}

.detail-page {
  background:
    radial-gradient(circle at top left, #fff2f7 0, transparent 32%),
    radial-gradient(circle at top right, #fff7eb 0, transparent 28%),
    linear-gradient(180deg, #fcf8f4 0%, #f5ede5 100%);
}

.back-link {
  margin-bottom: 14px;
}

.detail-hero,
.detail-section {
  padding: 24px;
}

.detail-section {
  margin-top: 18px;
}

.detail-meta {
  margin-top: 16px;
  padding: 16px;
  border-radius: 20px;
  background: #fffdf9;
  border: 1px solid var(--line);
}

.detail-meta-row {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.detail-meta-row strong {
  display: inline-block;
  min-width: 82px;
  color: var(--text);
}

.section-title-row h2 {
  margin: 0;
  font-size: 24px;
}

.section-title-row p {
  margin: 8px 0 0;
  color: var(--muted);
  line-height: 1.7;
}

.detail-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  margin-top: 18px;
}

.detail-image {
  width: 100%;
  display: block;
  border-radius: 22px;
  background: linear-gradient(180deg, #f7dbe3 0%, #f7efe2 100%);
  border: 1px solid var(--line);
  box-shadow: 0 14px 32px rgba(78, 49, 34, 0.10);
}

.image-card {
  margin: 0;
}

.image-open-link {
  display: block;
  text-decoration: none;
}

.image-caption {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 16px;
  background: rgba(255, 253, 250, 0.84);
  color: var(--muted);
  font-size: 13px;
}

.image-actions {
  display: inline-flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.image-actions a {
  color: var(--accent-strong);
  font-weight: 700;
  text-decoration: none;
}

.markdown-body {
  margin-top: 18px;
  padding: 22px;
  border-radius: 22px;
  background: #fffefb;
  border: 1px solid var(--line);
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3 {
  margin: 28px 0 12px;
  line-height: 1.35;
}

.markdown-body h1 { font-size: 28px; }
.markdown-body h2 { font-size: 22px; }
.markdown-body h3 { font-size: 18px; }

.markdown-body p,
.markdown-body li {
  color: var(--text);
  line-height: 1.9;
  font-size: 15px;
}

.markdown-body ul {
  margin: 10px 0 0;
  padding-left: 20px;
}

.markdown-body code {
  padding: 2px 6px;
  border-radius: 8px;
  background: #f7ece8;
  font-family: "Consolas", "SFMono-Regular", monospace;
  font-size: 0.95em;
}

.markdown-body pre {
  overflow-x: auto;
  padding: 14px;
  border-radius: 16px;
  background: #f8f0ea;
}

@media (max-width: 820px) {
  .hero {
    grid-template-columns: 1fr;
  }
}
"""


def _app_js() -> str:
    return """const state = {
  items: [],
  filter: "all",
  query: "",
};

async function boot() {
  const response = await fetch("./data.json");
  const payload = await response.json();
  state.items = payload.items || [];
  document.getElementById("itemCount").textContent = `${state.items.length} 条`;
  bindUI();
  render();
}

function bindUI() {
  const input = document.getElementById("searchInput");
  input.addEventListener("input", (event) => {
    state.query = event.target.value.trim().toLowerCase();
    render();
  });

  document.querySelectorAll(".filter-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".filter-chip").forEach((node) => node.classList.remove("is-active"));
      chip.classList.add("is-active");
      state.filter = chip.dataset.filter;
      render();
    });
  });
}

function render() {
  const cards = document.getElementById("cards");
  const filtered = state.items.filter((item) => {
    const matchesFilter = state.filter === "all" || item.content_type === state.filter;
    const haystack = [
      item.title,
      item.summary,
      item.hook,
      item.title_option,
      item.opening,
      item.body,
      item.closing,
      ...(item.tags || []),
    ].join(" ").toLowerCase();
    const matchesQuery = !state.query || haystack.includes(state.query);
    return matchesFilter && matchesQuery;
  });

  cards.innerHTML = filtered.length
    ? filtered.map(renderCard).join("")
    : `<article class="card"><div class="card-body"><h2 class="card-title">暂时没有匹配内容</h2><p class="card-copy">你可以换个关键词，或者先在本地多跑几次生成库存。</p></div></article>`;
}

function renderCard(item) {
  const coverSrc = item.cover_url || (item.gallery_urls && item.gallery_urls[0]) || "";
  const tags = (item.tags || []).slice(0, 5).map((tag) => `<span class="tag">#${escapeHtml(tag)}</span>`).join("");
  const coverDesign = item.cover_design && item.cover_design.template
    ? `<div><strong>封面风格：</strong>${escapeHtml(item.cover_design.template)} / ${escapeHtml(item.cover_design.palette || "")}</div>`
    : "";

  return `
    <article class="card">
      ${coverSrc ? `<img class="card-cover" src="${coverSrc}" alt="">` : `<div class="card-cover"></div>`}
      <div class="card-body">
        <span class="card-type">${escapeHtml(item.content_type || "内容库存")}</span>
        <h2 class="card-title">${escapeHtml(item.title_option || item.title || "未命名内容")}</h2>
        <p class="card-copy">${escapeHtml(item.opening || item.summary || "")}</p>
        <div class="tag-list">${tags}</div>
        <div class="meta-list">
          <div><strong>原始标题：</strong>${escapeHtml(item.title || "")}</div>
          <div><strong>生成时间：</strong>${escapeHtml(item.generated_at || "")}</div>
          ${item.price_text ? `<div><strong>价格：</strong>${escapeHtml(item.price_text)}</div>` : ""}
          ${coverDesign}
        </div>
        <div class="actions">
          ${item.detail_url ? `<a class="action-link" href="${item.detail_url}">看图片和正文</a>` : ""}
          ${item.source_url ? `<a class="action-link secondary" href="${item.source_url}" target="_blank" rel="noreferrer">看官网原链</a>` : ""}
        </div>
      </div>
    </article>
  `;
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

boot().catch((error) => {
  document.getElementById("cards").innerHTML = `<article class="card"><div class="card-body"><h2 class="card-title">站点加载失败</h2><p class="card-copy">${escapeHtml(error.message)}</p></div></article>`;
});
"""
