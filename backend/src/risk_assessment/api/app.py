"""Build the web app, and plug the real storage and AI into it: the composition root."""

import logging
from collections.abc import Callable
from typing import ClassVar

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from risk_assessment.ai.challenge import AiChallengeAsker
from risk_assessment.ai.model import LanguageModel
from risk_assessment.ai.providers import claude
from risk_assessment.ai.ranking import AiTake5Ranker
from risk_assessment.ai.vague_hazard import AiHazardJudge
from risk_assessment.api.errors import add_error_handlers
from risk_assessment.api.ranking_routes import create_ranking_router
from risk_assessment.api.take5_routes import create_router
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from risk_assessment.services.ports import (
    ChallengeAsker,
    HazardJudge,
    Take5Ranker,
    Take5Repository,
)
from risk_assessment.services.ranking import Take5RankingService
from risk_assessment.services.take5s import Take5Service
from risk_assessment.settings import AiProvider, Settings
from risk_assessment.storage.sqlite import SqliteTake5Repository

_logger: logging.Logger = logging.getLogger(__name__)


class _ProviderModels(BaseModel):
    """How to reach one provider's models.

    Attributes:
        build: Builds a model from the key and the model's name (None for the
            provider's default).
        quick_model: The provider's fastest model, for short jobs (decision D61).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    build: Callable[[str, str | None], LanguageModel]
    quick_model: str


# Adding a provider is one adapter file and one line here.
_PROVIDERS: dict[AiProvider, _ProviderModels] = {
    AiProvider.CLAUDE: _ProviderModels(
        build=claude.ClaudeModel,
        quick_model=claude.QUICK_MODEL,
    ),
}


def create_app(
    repository: Take5Repository | None = None,
    settings: Settings | None = None,
    challenge_asker: ChallengeAsker | None = None,
    hazard_judge: HazardJudge | None = None,
    take5_ranker: Take5Ranker | None = None,
) -> FastAPI:
    """Build the API.

    Args:
        repository: Where Take 5s are kept. Tests pass their own; by default it is
            the SQLite file named in the settings.
        settings: The settings to use. By default they are read from the environment.
        challenge_asker: What writes the challenge question. Tests pass a stand-in.
            By default it is the AI named in the settings, or none when no key is
            set, so the fixed question is asked every time (spec C3).
        hazard_judge: What judges whether a hazard is vague. Tests pass a stand-in.
            By default it is the AI named in the settings, or none when no key is
            set, so the word rule decides every time (spec T6).
        take5_ranker: What reorders the worst Take 5s. Tests pass a stand-in. By
            default it is the AI named in the settings, or none when no key is set,
            so the fixed rules rank them alone (spec W6).

    Returns:
        The FastAPI app.
    """
    _show_app_logs()
    app_settings: Settings = settings or Settings()
    storage: Take5Repository = (
        repository
        if repository is not None
        else SqliteTake5Repository(app_settings.database_path)
    )
    app = FastAPI(title="Take 5", version="0.1.0")
    add_error_handlers(app)
    service = Take5Service(
        storage,
        BOOKLET_TEMPLATE,
        challenge_asker=(
            challenge_asker
            if challenge_asker is not None
            else build_challenge_asker(app_settings)
        ),
        hazard_judge=(
            hazard_judge
            if hazard_judge is not None
            else build_hazard_judge(app_settings)
        ),
    )
    app.include_router(create_router(service))
    ranking_service = Take5RankingService(
        storage,
        take5_ranker if take5_ranker is not None else build_take5_ranker(app_settings),
    )
    app.include_router(create_ranking_router(ranking_service))
    return app


def _show_app_logs() -> None:
    """Show the app's own info lines in the server's log, beside uvicorn's.

    `start.py` gives uvicorn `backend/dev_logging.json`, which sets this logger up, so
    this does nothing then. Without it, as in the tests or a server started by hand,
    Python shows the app's warnings and nothing less, and lines such as which model asks
    would be lost.
    """
    app_logger: logging.Logger = logging.getLogger("risk_assessment")
    if app_logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s:     %(name)s: %(message)s"))
    app_logger.addHandler(handler)
    app_logger.setLevel(logging.INFO)


def build_challenge_asker(settings: Settings) -> ChallengeAsker | None:
    """Build the AI that writes the challenge question, if a key is set.

    Args:
        settings: The provider, model and key to use.

    Returns:
        An asker for the provider's model, or None when no key is set.
    """
    ai_key: str | None = settings.usable_ai_key
    if ai_key is None:
        _logger.info("No AI key is set, so the fixed question is always asked.")
        return None
    provider: _ProviderModels = _PROVIDERS[settings.ai_provider]
    model: LanguageModel = provider.build(ai_key, settings.ai_model)
    _logger.info("The challenge question is asked of %s.", model.name)
    return AiChallengeAsker(model)


def build_hazard_judge(settings: Settings) -> HazardJudge | None:
    """Build the AI that judges whether a hazard is vague, if a key is set.

    Args:
        settings: The provider, hazard model and key to use.

    Returns:
        A judge for the provider's hazard model (its quick model unless the settings
        name another), or None when no key is set.
    """
    ai_key: str | None = settings.usable_ai_key
    if ai_key is None:
        _logger.info("No AI key is set, so the word rule judges every hazard.")
        return None
    provider: _ProviderModels = _PROVIDERS[settings.ai_provider]
    model: LanguageModel = provider.build(
        ai_key,
        settings.ai_hazard_model or provider.quick_model,
    )
    _logger.info("Vague hazards are judged by %s.", model.name)
    return AiHazardJudge(model)


def build_take5_ranker(settings: Settings) -> Take5Ranker | None:
    """Build the AI that reorders the worst Take 5s, if a key is set.

    It uses the same model as the challenge question, since both read whole Take 5s.

    Args:
        settings: The provider, model and key to use.

    Returns:
        A ranker for the provider's model, or None when no key is set.
    """
    ai_key: str | None = settings.usable_ai_key
    if ai_key is None:
        _logger.info("No AI key is set, so the fixed rules rank Take 5s alone.")
        return None
    provider: _ProviderModels = _PROVIDERS[settings.ai_provider]
    model: LanguageModel = provider.build(ai_key, settings.ai_model)
    _logger.info("Take 5s are ranked by %s.", model.name)
    return AiTake5Ranker(model)
