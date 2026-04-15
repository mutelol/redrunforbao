from __future__ import annotations

from pathlib import Path

from curly_agent.config import AgentConfig
from curly_agent.site import build_static_site


def main() -> int:
    config = AgentConfig.load(Path("curly-agent.config.json"))
    site_index = build_static_site(
        project_root=Path.cwd(),
        runs_root=Path(config.output_root),
        site_root=Path(config.site_output),
    )
    print(f"站点已生成: {site_index.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
