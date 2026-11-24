"""Settings read from the environment, so a deployment changes none of the code."""

from enum import StrEnum
from pathlib import Path
from typing import ClassVar

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_FOLDER: Path = Path(__file__).parents[2]
_DEFAULT_DATABASE_PATH: Path = _BACKEND_FOLDER / ".data/take5.sqlite3"
# A file of `NAME=value` lines on the developer's own computer. Git ignores it.
_LOCAL_SETTINGS_FILE: Path = _BACKEND_FOLDER / ".env"


class AiProvider(StrEnum):
    """Which company's AI does the app's AI jobs, such as the challenge question."""

    CLAUDE = "claude"
    # OpenAI's models, as ChatGPT uses (task 0045). Its API key is billed apart from
    # a ChatGPT subscription.
    CHATGPT = "chatgpt"


class Settings(BaseSettings):
    """The app's settings. Each one can be set with a `TAKE5_` environment variable.

    A setting can also go in `backend/.env`, as a line such as `TAKE5_AI_KEY=...`.
    An environment variable wins over that file.

    Attributes:
        database_path: Where the SQLite file is kept (`TAKE5_DATABASE_PATH`). By
            default it is `backend/.data/take5.sqlite3`, which git ignores.
        ai_provider: Whose AI does every AI job (`TAKE5_AI_PROVIDER`): `claude`, the
            default, or `chatgpt` (task 0045).
        ai_model: Which of that provider's models writes the challenge question
            (`TAKE5_AI_MODEL`). None means the provider's own default.
        ai_hazard_model: Which of that provider's models judges vague hazards
            (`TAKE5_AI_HAZARD_MODEL`). None means the provider's quick model
            (decision D61).
        ai_scan_model: Which of that provider's models reads photos of paper cards
            (`TAKE5_AI_SCAN_MODEL`, task 0033). None means the main model, `ai_model`.
        ai_key: The key for the chosen provider's API (`TAKE5_AI_KEY`): Anthropic's
            for Claude, OpenAI's for ChatGPT. With none, or an empty one, no AI is
            asked: the fixed question is used (spec C3) and the word rule judges
            hazards (spec T6).
        rank_today_only: Whether the ranking counts only today's Take 5s
            (`TAKE5_RANK_TODAY_ONLY`). False, the default while the app is a proof of
            concept, ranks every saved Take 5 (spec W7, decision D118).
        area_last_30_days_only: Whether risk by area counts only the last 30 days
            (`TAKE5_AREA_LAST_30_DAYS_ONLY`). False, the default while the app is a
            proof of concept, counts every saved Take 5 (spec A2, decision D119).
    """

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="TAKE5_",
        env_file=_LOCAL_SETTINGS_FILE,
        # Also reads a file saved as UTF-8 with a byte order mark, as Windows can.
        env_file_encoding="utf-8-sig",
        extra="ignore",
        frozen=True,
    )

    database_path: Path = _DEFAULT_DATABASE_PATH
    ai_provider: AiProvider = AiProvider.CLAUDE
    ai_model: str | None = None
    ai_hazard_model: str | None = None
    ai_scan_model: str | None = None
    ai_key: SecretStr | None = None
    rank_today_only: bool = False
    area_last_30_days_only: bool = False

    @property
    def usable_ai_key(self) -> str | None:
        """The AI key without spaces at its ends, if one is set.

        Returns:
            The key, or None when it is not set or is only spaces.
        """
        if self.ai_key is None:
            return None
        return self.ai_key.get_secret_value().strip() or None
