from __future__ import annotations

import hashlib
from pathlib import Path

from .config import AgentConfig
from .models import CandidateItem
from .scraper import fetch_bytes
from .utils import as_data_uri, ensure_dir, guess_extension_from_url, mime_type_from_extension


def download_candidate_images(item: CandidateItem, config: AgentConfig, assets_dir: Path) -> list[Path]:
    ensure_dir(assets_dir)
    image_paths: list[Path] = []
    for index, image_url in enumerate(item.detail_images[:4] or [item.image_url], start=1):
        ext = guess_extension_from_url(image_url)
        label = "primary" if index == 1 else f"detail-{index}"
        output_path = assets_dir / f"{label}{ext}"
        try:
            output_path.write_bytes(fetch_bytes(image_url, config))
            image_paths.append(output_path)
        except Exception:
            continue
    return image_paths


def choose_cover_design(item: CandidateItem, main_line: str, secondary_line: str) -> dict[str, str]:
    palettes = [
        {
            "name": "strawberry-milk",
            "bg_top": "#fff4f8",
            "bg_bottom": "#f6d7df",
            "surface": "#fff9fb",
            "chip": "#ffdbe6",
            "title": "#473246",
            "body": "#6e5d67",
            "accent": "#8b5165",
        },
        {
            "name": "butter-cream",
            "bg_top": "#fff9ef",
            "bg_bottom": "#f3e3bf",
            "surface": "#fffdf7",
            "chip": "#ffe7a8",
            "title": "#524131",
            "body": "#7a6956",
            "accent": "#a26d31",
        },
        {
            "name": "mint-soda",
            "bg_top": "#f1fffb",
            "bg_bottom": "#ccefe7",
            "surface": "#fbfffe",
            "chip": "#c4efe3",
            "title": "#30433f",
            "body": "#5a6f69",
            "accent": "#347564",
        },
        {
            "name": "sky-jelly",
            "bg_top": "#f2f8ff",
            "bg_bottom": "#d5e7ff",
            "surface": "#fbfdff",
            "chip": "#d7e8ff",
            "title": "#33415a",
            "body": "#61708a",
            "accent": "#506da4",
        },
    ]
    templates = ["editorial-left", "stacked-card", "sticker-frame", "split-focus"]
    seed = f"{item.url}|{item.title}|{main_line}|{secondary_line}"
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    palette = palettes[digest[0] % len(palettes)]
    template = templates[digest[1] % len(templates)]
    return {"template": template, **palette}


def write_cover_svg(
    svg_path: Path,
    item: CandidateItem,
    image_paths: list[Path],
    main_line: str,
    secondary_line: str,
    accent_line: str,
) -> tuple[Path, dict[str, str]]:
    if not image_paths:
        raise RuntimeError("没有成功下载到可用图片，无法生成封面。")
    primary_path = image_paths[0]
    primary_bytes = primary_path.read_bytes()
    primary_uri = as_data_uri(primary_bytes, mime_type_from_extension(primary_path.suffix))
    design = choose_cover_design(item, main_line, secondary_line)

    line1, _, line2 = main_line.partition("\n")
    svg = _render_template_svg(
        template=design["template"],
        palette=design,
        primary_uri=primary_uri,
        line1=line1,
        line2=line2 or line1,
        secondary_line=secondary_line,
        accent_line=accent_line,
    )
    svg_path.write_text(svg, encoding="utf-8")
    return svg_path, design


def _render_template_svg(
    template: str,
    palette: dict[str, str],
    primary_uri: str,
    line1: str,
    line2: str,
    secondary_line: str,
    accent_line: str,
) -> str:
    common_defs = f"""<defs>
    <filter id="blurBg">
      <feGaussianBlur stdDeviation="26" />
    </filter>
    <linearGradient id="overlay" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{palette['bg_top']}" stop-opacity="0.24"/>
      <stop offset="100%" stop-color="{palette['bg_bottom']}" stop-opacity="0.85"/>
    </linearGradient>
  </defs>"""

    if template == "editorial-left":
        body = f"""
  <image href="{primary_uri}" x="-80" y="-120" width="1240" height="1680" preserveAspectRatio="xMidYMid slice" filter="url(#blurBg)"/>
  <rect x="0" y="0" width="1080" height="1440" fill="url(#overlay)"/>
  <rect x="74" y="88" width="932" height="1264" rx="52" fill="{palette['surface']}" opacity="0.84"/>
  <image href="{primary_uri}" x="120" y="148" width="560" height="760" preserveAspectRatio="xMidYMid slice"/>
  <rect x="120" y="148" width="560" height="760" fill="#ffffff" opacity="0.05"/>
  <g transform="translate(120 965)">
    <rect x="0" y="0" width="520" height="72" rx="36" fill="{palette['chip']}"/>
    <text x="34" y="47" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="28" font-weight="700" fill="{palette['accent']}">{secondary_line}</text>
  </g>
  <text x="740" y="275" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="74" font-weight="800" fill="{palette['title']}">{line1}</text>
  <text x="740" y="365" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="74" font-weight="800" fill="{palette['title']}">{line2}</text>
  <text x="120" y="1085" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="30" font-weight="700" fill="{palette['accent']}">{accent_line}</text>
  <text x="120" y="1140" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="22" fill="{palette['body']}">建议发布前手动调整裁切、背景和文字位置</text>
"""
    elif template == "stacked-card":
        body = f"""
  <image href="{primary_uri}" x="-100" y="-60" width="1280" height="1560" preserveAspectRatio="xMidYMid slice" filter="url(#blurBg)"/>
  <rect x="0" y="0" width="1080" height="1440" fill="url(#overlay)"/>
  <rect x="88" y="92" width="904" height="1256" rx="58" fill="{palette['surface']}" opacity="0.9"/>
  <rect x="138" y="150" width="804" height="780" rx="44" fill="#ffffff" opacity="0.92"/>
  <image href="{primary_uri}" x="168" y="180" width="744" height="720" preserveAspectRatio="xMidYMid slice"/>
  <g transform="translate(138 980)">
    <rect x="0" y="0" width="240" height="62" rx="31" fill="{palette['chip']}"/>
    <text x="24" y="40" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="24" font-weight="700" fill="{palette['accent']}">{accent_line}</text>
  </g>
  <text x="138" y="1090" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="82" font-weight="800" fill="{palette['title']}">{line1}</text>
  <text x="138" y="1182" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="82" font-weight="800" fill="{palette['title']}">{line2}</text>
  <text x="138" y="1270" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="28" font-weight="700" fill="{palette['accent']}">{secondary_line}</text>
  <text x="138" y="1318" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="22" fill="{palette['body']}">Curly Collection cover template</text>
"""
    elif template == "sticker-frame":
        body = f"""
  <image href="{primary_uri}" x="-120" y="-80" width="1320" height="1600" preserveAspectRatio="xMidYMid slice" filter="url(#blurBg)"/>
  <rect x="0" y="0" width="1080" height="1440" fill="url(#overlay)"/>
  <g transform="rotate(-3 540 720)">
    <rect x="180" y="110" width="720" height="900" rx="34" fill="#fffefc"/>
    <image href="{primary_uri}" x="215" y="145" width="650" height="830" preserveAspectRatio="xMidYMid slice"/>
  </g>
  <rect x="122" y="1015" width="836" height="265" rx="46" fill="{palette['surface']}" opacity="0.95"/>
  <rect x="152" y="1048" width="196" height="58" rx="29" fill="{palette['chip']}"/>
  <text x="178" y="1086" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="24" font-weight="700" fill="{palette['accent']}">{secondary_line}</text>
  <text x="152" y="1168" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="76" font-weight="800" fill="{palette['title']}">{line1}</text>
  <text x="152" y="1254" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="76" font-weight="800" fill="{palette['title']}">{line2}</text>
  <text x="152" y="1310" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="24" fill="{palette['body']}">{accent_line}</text>
"""
    else:
        body = f"""
  <image href="{primary_uri}" x="-90" y="-120" width="1260" height="1680" preserveAspectRatio="xMidYMid slice" filter="url(#blurBg)"/>
  <rect x="0" y="0" width="1080" height="1440" fill="url(#overlay)"/>
  <rect x="96" y="96" width="888" height="1248" rx="56" fill="{palette['surface']}" opacity="0.85"/>
  <image href="{primary_uri}" x="132" y="132" width="816" height="620" preserveAspectRatio="xMidYMid slice"/>
  <rect x="132" y="132" width="816" height="620" fill="#ffffff" opacity="0.04"/>
  <rect x="132" y="790" width="816" height="410" rx="38" fill="#ffffff" opacity="0.86"/>
  <text x="172" y="920" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="30" font-weight="700" fill="{palette['accent']}">{secondary_line}</text>
  <text x="172" y="1020" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="84" font-weight="800" fill="{palette['title']}">{line1}</text>
  <text x="172" y="1114" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="84" font-weight="800" fill="{palette['title']}">{line2}</text>
  <text x="172" y="1195" font-family="'Microsoft YaHei', 'PingFang SC', sans-serif" font-size="26" fill="{palette['body']}">{accent_line}</text>
"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1440" viewBox="0 0 1080 1440">
  {common_defs}
  {body}
</svg>
"""
