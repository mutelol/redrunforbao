from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from curly_agent.config import AgentConfig
from curly_agent.content import build_content_pack
from curly_agent.history import HistoryStore
from curly_agent.output import create_run_directory, write_run_outputs
from curly_agent.scraper import enrich_candidate, fetch_homepage, parse_homepage, select_candidate
from curly_agent.site import build_static_site


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Curly Collection 小红书内容助手")
    parser.add_argument(
        "--config",
        default="curly-agent.config.json",
        help="配置文件路径，默认使用项目根目录下的 curly-agent.config.json",
    )
    parser.add_argument("--homepage-url", help="覆盖配置中的官网首页 URL")
    parser.add_argument("--output-root", help="覆盖配置中的输出目录")
    parser.add_argument(
        "--allow-seen",
        action="store_true",
        help="允许重复选择历史上已经生成过内容的产品",
    )
    parser.add_argument(
        "--no-download-images",
        action="store_true",
        help="只生成内容包，不下载图片素材",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = AgentConfig.load(Path(args.config))

    if args.homepage_url:
        config.homepage_url = args.homepage_url
    if args.output_root:
        config.output_root = args.output_root
    if args.no_download_images:
        config.download_images = False

    history = HistoryStore(Path(config.db_path))
    history.initialize()
    history.import_existing_runs(Path(config.output_root))

    homepage_html = fetch_homepage(config)
    candidates = parse_homepage(homepage_html, config.homepage_url)
    seen_state = history.seen_state()
    candidate_pool = history.unseen_items(candidates, seen_state)
    if not candidate_pool:
        if args.allow_seen:
            candidate_pool = candidates
        else:
            raise RuntimeError(
                "首页当前候选都已经生成过内容了。今天想避免重复的话，先别发；"
                "如果你就是想复用旧题材，可以加 --allow-seen。"
            )

    selection = select_candidate(candidate_pool, allow_fallback=config.allow_fallback)
    candidate = enrich_candidate(selection.item, config)
    content_pack = build_content_pack(candidate, selection.reason)

    run_dir = create_run_directory(Path(config.output_root), candidate)
    output_paths = write_run_outputs(
        run_dir=run_dir,
        config=config,
        selected_item=candidate,
        selection_reason=selection.reason,
        content_pack=content_pack,
        homepage_url=config.homepage_url,
    )
    history.record_generated(
        candidate,
        generated_at=datetime.now().isoformat(timespec="seconds"),
        run_dir=run_dir,
    )
    site_index = build_static_site(
        project_root=Path.cwd(),
        runs_root=Path(config.output_root),
        site_root=Path(config.site_output),
    )

    print(f"已生成内容包: {output_paths['content_pack']}")
    print(f"元数据文件: {output_paths['metadata']}")
    if "cover_svg" in output_paths:
        print(f"封面草稿: {output_paths['cover_svg']}")
    if "assets_dir" in output_paths:
        print(f"素材目录: {output_paths['assets_dir']}")
    print(f"静态站点: {site_index.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
