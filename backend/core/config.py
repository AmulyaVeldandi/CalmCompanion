"""Application settings for the CalmCompanion backend."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    app_name: str = "CalmCompanion API"
    allow_origins: tuple[str, ...] = ("*",)  # demo; lock down in production
    max_turns_kept: int = 200
    summary_window: int = 5

settings = Settings()
