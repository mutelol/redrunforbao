from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .assets import download_candidate_images, write_cover_svg
from .config import AgentConfig
from .models import CandidateItem
from .utils import ensure_dir, safe_slug


def create_run_directory(output_root: Path, item: CandidateItem) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    item_hint = item.item_id or item.url.rstrip("/").split("/")[-1] or item.source_section
    slug = safe_slug(f"{item.source_section}-{item_hint}")
    run_dir = output_root / f"{stamp}-{slug}"
    suffix = 2
    while run_dir.exists():
        run_dir = output_root / f"{stamp}-{slug}-{suffix}"
        suffix += 1
    run_dir = ensure_dir(run_dir)
    return run_dir


def write_run_outputs(
    run_dir: Path,
    config: AgentConfig,
    selected_item: CandidateItem,
    selection_reason: str,
    content_pack: dict[str, object],
    homepage_url: str,
) -> dict[str, str]:
    assets_dir = ensure_dir(run_dir / "assets")
    output_paths: dict[str, str] = {}
    downloaded: list[Path] = []

    if config.download_images:
        downloaded = download_candidate_images(selected_item, config, assets_dir)
        cover = content_pack["cover"]
        cover_svg, cover_design = write_cover_svg(
            assets_dir / "cover.svg",
            selected_item,
            downloaded,
            main_line=cover["main_cover_line"],
            secondary_line=cover["secondary_cover_line"],
            accent_line=cover["accent_line"],
        )
        content_pack["image_plan"]["cover_design"] = {
            "template": cover_design["template"],
            "palette": cover_design["name"],
        }
        output_paths["cover_svg"] = str(cover_svg.resolve())
        output_paths["assets_dir"] = str(assets_dir.resolve())

    content_path = run_dir / "content-pack.md"
    metadata_path = run_dir / "metadata.json"

    content_path.write_text(
        _render_markdown(
            item=selected_item,
            selection_reason=selection_reason,
            content_pack=content_pack,
            assets=downloaded,
        ),
        encoding="utf-8",
    )
    metadata_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "homepage_url": homepage_url,
                "selection_reason": selection_reason,
                "selected_item": selected_item.to_dict(),
                "content_pack": content_pack,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    output_paths["content_pack"] = str(content_path.resolve())
    output_paths["metadata"] = str(metadata_path.resolve())
    return output_paths


def _render_markdown(
    item: CandidateItem,
    selection_reason: str,
    content_pack: dict[str, object],
    assets: list[Path],
) -> str:
    brief = content_pack["post_brief"]
    cover = content_pack["cover"]
    draft = content_pack["post_draft"]
    image_plan = content_pack["image_plan"]
    tags = " ".join(f"#{tag}" for tag in content_pack["tags"])
    image_paths = "\n".join(f"- {path.name}" for path in assets) if assets else "- 本次未下载图片"
    detail_images = "\n".join(f"- {url}" for url in image_plan["detail_images"]) or "- 暂无"
    editing_notes = "\n".join(f"- {note}" for note in image_plan["editing_notes"])
    cover_design = image_plan.get("cover_design")
    cover_design_block = ""
    if isinstance(cover_design, dict):
        cover_design_block = (
            f"- Cover template: {cover_design['template']}\n"
            f"- Cover palette: {cover_design['palette']}\n"
        )
    hooks = "\n".join(f"- {hook}" for hook in content_pack["hooks"])
    titles = "\n".join(f"- {title}" for title in content_pack["titles"])
    comments = "\n".join(f"- {comment}" for comment in content_pack["comment_seeds"])
    checklist = "\n".join(f"- {line}" for line in content_pack["review_checklist"])

    return f"""# Curly Collection 内容包

## 1. 选题摘要

- 选题类型：{item.content_type}
- 来源分区：{item.source_section}
- 标题原文：{item.title}
- 来源链接：{item.url}
- 选择原因：{selection_reason}

{content_pack["summary"]}

## 2. Post Brief

- Goal: {brief["goal"]}
- Audience: {brief["audience"]}
- Core angle: {brief["core_angle"]}
- Desired reader action: {brief["desired_reader_action"]}

## 3. Hook Options

{hooks}

## 4. Title Options

{titles}

## 5. Cover Copy

- Main cover line:
  {cover["main_cover_line"]}
- Secondary cover line:
  {cover["secondary_cover_line"]}
- Accent line:
  {cover["accent_line"]}

## 6. Post Draft

- Opening:
  {draft["opening"]}

- Body:
{draft["body"]}

- Closing:
  {draft["closing"]}

## 7. Tags

{tags}

## 8. Comment Seeds

{comments}

## 9. Manual Review Checklist

{checklist}

## 10. Image Plan

- Hero image: {image_plan["hero_image"]}
- Layout:
  {image_plan["layout"]}
{cover_design_block}
- Detail images:
{detail_images}
- Editing notes:
{editing_notes}

## 11. Local Assets

{image_paths}
"""
