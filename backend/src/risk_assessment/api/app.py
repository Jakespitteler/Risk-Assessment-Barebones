"""Build the web app, and plug the real storage into it: the one composition root."""

from fastapi import FastAPI

from risk_assessment.api.errors import add_error_handlers
from risk_assessment.api.take5_routes import create_router
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from risk_assessment.services.ports import ChallengeAsker, Take5Repository
from risk_assessment.services.take5s import Take5Service
from risk_assessment.settings import Settings
from risk_assessment.storage.sqlite import SqliteTake5Repository


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
        challenge_asker: The AI that writes the challenge question. Tests pass a
            stand-in. Until an AI is plugged in (task 0009) there is none, so the
            fixed question is asked every time (spec C3).

    Returns:
        The FastAPI app.
    """
    storage: Take5Repository = (
        repository
        if repository is not None
        else SqliteTake5Repository((settings or Settings()).database_path)
    )
    app = FastAPI(title="Take 5", version="0.1.0")
    add_error_handlers(app)
    service = Take5Service(
        storage,
        BOOKLET_TEMPLATE,
        challenge_asker=challenge_asker,
    )
    app.include_router(create_router(service))
    return app
