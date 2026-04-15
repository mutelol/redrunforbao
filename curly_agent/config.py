from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentConfig:
    homepage_url: str
    output_root: str
    db_path: str
    site_output: str
    language: str
    voice: str
    download_images: bool
    allow_fallback: bool
    timeout_seconds: int = 20

    @classmethod
    def load(cls, path: Path) -> "AgentConfig":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            homepage_url=data["homepage_url"],
            output_root=data["output_root"],
            db_path=data.get("db_path", "curly-agent.sqlite3"),
            site_output=data.get("site_output", "site"),
            language=data.get("language", "zh-CN"),
            voice=data.get("voice", "female-friendly-light-share"),
            download_images=bool(data.get("download_images", True)),
            allow_fallback=bool(data.get("allow_fallback", True)),
            timeout_seconds=int(data.get("timeout_seconds", 20)),
        )
