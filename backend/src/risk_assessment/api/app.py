"""Build the web app, and plug the real storage and AI into it: the composition root."""

import logging
from collections.abc import Callable

from fastapi import FastAPI

from risk_assessment.ai.challenge import AiChallengeAsker
from risk_assessment.ai.model import LanguageModel
from risk_assessment.ai.providers.claude import ClaudeModel
from risk_assessment.api.errors import add_error_handlers
from risk_assessment.api.take5_routes import create_router
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from risk_assessment.services.ports import ChallengeAsker, Take5Repository
from risk_assessment.services.take5s import Take5Service
from risk_assessment.settings import AiProvider, Settings
from risk_assessment.storage.sqlite import SqliteTake5Repository

_logger: logging.Logger = logging.getLogger(__name__)

# How to build each provider's model from its key and model name (None for its
# default). Adding a provider is one adapter file and one line here.
_LANGUAGE_MODELS: dict[AiProvider, Callable[[str, str | None], LanguageModel]] = {
    AiProvider.CLAUDE: ClaudeModel,
}


def create_app(
    repository: Take5Repository | None = None,
    settings: Settings | None = None,
    challenge_asker: ChallengeAsker | None = None,
) -> FastAPI:
    """Build the API.

    Args:
        repository: Where Take 5s are kept. Tests pass their own; by default it is
            the SQLite file named in the settings.
        settings: The settings to use. By default they are read from the environment.
        challenge_asker: What writes the challenge question. Tests pass a stand-in.
            By default it is the AI named in the settings, or none when no key is
            set, so the fixed question is asked every time (spec C3).

    Returns:
        The FastAPI app.
    """
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
        challenge_asker=challenge_asker or build_challenge_asker(app_settings),
    )
    app.include_router(create_router(service))
    return app


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
    build_model: Callable[[str, str | None], LanguageModel] = _LANGUAGE_MODELS[
        settings.ai_provider
    ]
    model: LanguageModel = build_model(ai_key, settings.ai_model)
    _logger.info("The challenge question is asked of %s.", model.name)
    return AiChallengeAsker(model)
