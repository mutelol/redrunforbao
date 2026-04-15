from __future__ import annotations

import re
import urllib.request
from typing import Iterable

from .config import AgentConfig
from .models import CandidateItem, SelectionResult
from .utils import absolute_url, clean_text, collapse_spaces, normalized_request_url, unique_preserve_order

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


def fetch_text(url: str, config: AgentConfig) -> str:
    request = urllib.request.Request(normalized_request_url(url), headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
        return response.read().decode("utf-8", "ignore")


def fetch_bytes(url: str, config: AgentConfig) -> bytes:
    request = urllib.request.Request(normalized_request_url(url), headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
        return response.read()


def fetch_homepage(config: AgentConfig) -> str:
    return fetch_text(config.homepage_url, config)


def parse_homepage(html: str, base_url: str) -> list[CandidateItem]:
    candidates = []
    candidates.extend(_parse_news_section(html, base_url))
    candidates.extend(_parse_arrivals_section(html, base_url))
    deduped: list[CandidateItem] = []
    seen_urls: set[str] = set()
    for item in candidates:
        if item.url not in seen_urls:
            seen_urls.add(item.url)
            deduped.append(item)
    return deduped


def _parse_news_section(html: str, base_url: str) -> list[CandidateItem]:
    news_block = _slice_between(html, "CURLY'S NEWS", "NEW ARRIVALS")
    pattern = re.compile(
        r'<article class="articles__unit">.*?<a class="newslead" href="(?P<url>[^"]+)">.*?'
        r'<div class="articles__thumb" data-original="(?P<img>[^"]+)".*?</div>.*?'
        r'<h2 class="articles__ttl">(?P<title>.*?)</h2>.*?'
        r'<time datetime="(?P<date>[^"]+)">.*?</time>.*?'
        r'<div class="articles__desc[^"]*"[^>]*>(?P<desc>.*?)</div>',
        flags=re.I | re.S,
    )
    items: list[CandidateItem] = []
    for index, match in enumerate(pattern.finditer(news_block), start=1):
        items.append(
            CandidateItem(
                source_section="news",
                title=collapse_spaces(clean_text(match.group("title"))),
                url=absolute_url(base_url, match.group("url")),
                image_url=absolute_url(base_url, match.group("img")),
                position=index,
                description=collapse_spaces(clean_text(match.group("desc"))),
                published_at=match.group("date"),
                is_new=True,
                content_type="新品速递",
            )
        )
    return items


def _parse_arrivals_section(html: str, base_url: str) -> list[CandidateItem]:
    arrivals_block = _slice_after(html, "NEW ARRIVALS")
    pattern = re.compile(r'<div class="item"><div class="item__container">(?P<block>.*?)</div></div>', flags=re.I | re.S)
    items: list[CandidateItem] = []
    for index, match in enumerate(pattern.finditer(arrivals_block), start=1):
        block = match.group("block")
        url = _extract_first(r'<a href="([^"]+)"', block)
        image = _extract_first(r'data-original="([^"]+)"', block)
        title = _extract_first(r'<span class="item__name">(.*?)</span>', block)
        item_id = _extract_first(r'<span class="item__id">(.*?)</span>', block)
        price_html = _extract_between(block, '<span class="item__price price">', '<span class="item__id">')
        if not price_html:
            price_html = _extract_between(block, '<span class="item__price price">', '<span class="item__photo"')
        if not url or not title:
            continue
        items.append(
            CandidateItem(
                source_section="new_arrivals",
                title=collapse_spaces(clean_text(title)),
                url=absolute_url(base_url, url),
                image_url=absolute_url(base_url, image),
                position=index,
                price_text=_normalize_price(clean_text(price_html)),
                item_id=collapse_spaces(clean_text(item_id)),
                is_new="NEW" in price_html.upper(),
                content_type="新品速递",
            )
        )
    return items


def select_candidate(items: Iterable[CandidateItem], allow_fallback: bool = True) -> SelectionResult:
    items = list(items)
    if not items:
        raise RuntimeError("首页没有解析到候选内容，无法生成内容包。")

    scored = [(item, _score_candidate(item)) for item in items]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    best_item, score = scored[0]

    if score <= 0 and not allow_fallback:
        raise RuntimeError("候选内容存在，但没有满足规则的主选题。")

    if best_item.source_section != "new_arrivals" and not best_item.is_new:
        best_item.content_type = "旧款回看"

    reason = (
        f"选择了 {best_item.source_section} 区的第 {best_item.position} 项："
        f"图片可用、标题可读，综合得分 {score}。"
    )
    return SelectionResult(item=best_item, reason=reason)


def enrich_candidate(item: CandidateItem, config: AgentConfig) -> CandidateItem:
    detail_html = fetch_text(item.url, config)
    if "/products/detail/" in item.url:
        return _enrich_product(item, detail_html)
    return _enrich_article(item, detail_html)


def _enrich_product(item: CandidateItem, html: str) -> CandidateItem:
    title = _extract_first(r'<h1 class="item-detail__ttl"[^>]*>(.*?)</h1>', html)
    price = _extract_first(r'<p class="item-detail__price[^"]*"[^>]*>(.*?)</p>', html)
    body = _extract_between(html, 'itemprop="description">', '</div><!-- /.page-body -->')
    categories = re.findall(r'<a href="[^"]+">([^<]+)</a>', _extract_between(html, '<dt class="en-h">CATEGORY:</dt>', '</dl>'))
    images = _extract_product_images(html)

    item.title = collapse_spaces(clean_text(title or item.title))
    item.price_text = _normalize_price(clean_text(price or item.price_text))
    item.detail_text = clean_text(body)
    item.detail_images = unique_preserve_order([item.image_url, *images])
    item.categories = [collapse_spaces(clean_text(value)) for value in categories if collapse_spaces(clean_text(value))]
    item.highlights = _derive_highlights(item)
    item.uncertainties = _derive_uncertainties(item)
    return item


def _enrich_article(item: CandidateItem, html: str) -> CandidateItem:
    title = _extract_first(r'<h1 class="post-heading__ttl">.*?<a [^>]*>(.*?)</a>.*?</h1>', html)
    body = _extract_first(r'<div class="post-body page-style">(.*?)</div>\s*<!-- page-content -->', html)
    date = _extract_first(r'<time datetime="([^"]+)">', html)
    categories = re.findall(r'<dd class="local-footer__cat">.*?<a [^>]*>(.*?)</a>', html, flags=re.I | re.S)
    images = re.findall(r'(https://curlycollection\.jp/wp-content/uploads/[^"\']+)', html)

    item.title = collapse_spaces(clean_text(title or item.title))
    item.detail_text = clean_text(body)
    item.published_at = date or item.published_at
    item.detail_images = unique_preserve_order([item.image_url, *images])
    item.categories = [collapse_spaces(clean_text(value)) for value in categories if collapse_spaces(clean_text(value))]
    item.highlights = _derive_highlights(item)
    item.uncertainties = _derive_uncertainties(item)
    return item


def _derive_highlights(item: CandidateItem) -> list[str]:
    text = f"{item.title}\n{item.detail_text}"
    highlights: list[str] = []
    rules = [
        ("500ml", "细看容量描述，页面提到 500ml 水瓶也能放进去"),
        ("コットン100%", "材质写了 100% 棉，更适合走柔软、好搭配的分享口吻"),
        ("メッシュ", "有网眼或轻盈材质感，容易写出春夏感和出门搭配感"),
        ("チャーム", "带挂件或小配饰，细节上更有“可爱完成度”"),
        ("刺繍", "有刺绣元素，适合强调手感和小面积点缀的精致感"),
        ("ポーチ", "本身就是很适合做收纳感内容的小件单品"),
        ("バッグ", "包型单品更容易写出通勤、出门、挂包场景"),
        ("fabric", "可以从布料图案、DIY 灵感、手作感切入"),
        ("生地", "可以从布料图案、DIY 灵感、手作感切入"),
    ]
    for needle, sentence in rules:
        if needle.lower() in text.lower():
            highlights.append(sentence)

    if not highlights and item.description:
        highlights.append("首页简介已经给出基础卖点，适合做一条轻量的新品情报帖")
    if item.price_text:
        highlights.append(f"页面当前价格显示为 {item.price_text}，正文里可以保留成“以页面为准”的信息")
    return unique_preserve_order(highlights)[:4]


def _derive_uncertainties(item: CandidateItem) -> list[str]:
    uncertainties: list[str] = []
    if not item.price_text:
        uncertainties.append("页面上没有稳定解析出价格，正文里不要写死价格。")
    if len(item.detail_images) <= 1:
        uncertainties.append("详情页图片数量较少，配图时更依赖首图和封面排版。")
    if not item.detail_text:
        uncertainties.append("详情页正文较少，分享点要更多基于视觉和标题。")
    return uncertainties


def _score_candidate(item: CandidateItem) -> int:
    score = 0
    if item.source_section == "new_arrivals":
        score += 55
    else:
        score += 38
    if item.is_new:
        score += 18
    if item.image_url:
        score += 15
    if item.title:
        score += 10
    if item.description:
        score += 6
    score += max(0, 12 - item.position)

    attractive_keywords = [
        "kitty",
        "hello",
        "いちご",
        "チェリー",
        "リボン",
        "ポーチ",
        "バッグ",
        "チャーム",
        "刺繍",
        "ピンク",
    ]
    title_lower = item.title.lower()
    for keyword in attractive_keywords:
        if keyword in title_lower:
            score += 4
    if any(keyword in title_lower for keyword in ["バッグ", "ポーチ", "チャーム", "パスケース", "ショルダー"]):
        score += 18
    if any(keyword in title_lower for keyword in ["ファブリック", "fabric", "生地"]):
        score -= 18
    return score


def _slice_between(value: str, start_marker: str, end_marker: str) -> str:
    start = value.find(start_marker)
    if start == -1:
        return value
    end = value.find(end_marker, start + len(start_marker))
    if end == -1:
        return value[start:]
    return value[start:end]


def _slice_after(value: str, marker: str) -> str:
    start = value.find(marker)
    if start == -1:
        return value
    return value[start:]


def _extract_first(pattern: str, value: str) -> str:
    match = re.search(pattern, value, flags=re.I | re.S)
    if not match:
        return ""
    if match.lastindex:
        return match.group(1)
    return match.group(0)


def _extract_between(value: str, start_marker: str, end_marker: str) -> str:
    start = value.find(start_marker)
    if start == -1:
        return ""
    start += len(start_marker)
    end = value.find(end_marker, start)
    if end == -1:
        return value[start:]
    return value[start:end]


def _extract_product_images(html: str) -> list[str]:
    images = []
    for raw in re.findall(r'(/shop/upload/save_image/[^"\')\s]+)', html):
        if "icon_" in raw:
            continue
        if not re.search(r"\.(jpg|jpeg|png|webp)$", raw, flags=re.I):
            continue
        images.append(absolute_url("https://curlycollection.jp", raw))
    return unique_preserve_order(images)[:6]


def _normalize_price(value: str) -> str:
    value = collapse_spaces(value)
    value = value.replace("（税込）", "").strip()
    return value
