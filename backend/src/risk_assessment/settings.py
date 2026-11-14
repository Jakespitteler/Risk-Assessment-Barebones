"""Settings read from the environment, so a deployment changes none of the code."""

from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_DATABASE_PATH: Path = Path(__file__).parents[2] / ".data/take5.sqlite3"


class Settings(BaseSettings):
    """The app's settings. Each one can be set with a `TAKE5_` environment variable.

    Attributes:
        database_path: Where the SQLite file is kept (`TAKE5_DATABASE_PATH`). By
            default it is `backend/.data/take5.sqlite3`, which git ignores.
    """

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="TAKE5_",
        frozen=True,
    )

    database_path: Path = _DEFAULT_DATABASE_PATH
