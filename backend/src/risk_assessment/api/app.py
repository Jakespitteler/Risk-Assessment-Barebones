"""Build the web app and plug in the real repository in one composition root."""

import os
from pathlib import Path

from fastapi import FastAPI

from risk_assessment.api.take5_routes import create_router
from risk_assessment.domain.take5.template import BOOKLET_TEMPLATE
from risk_assessment.services.ports import Take5Repository
from risk_assessment.services.take5s import Take5Service
from risk_assessment.storage.sqlite import SqliteTake5Repository


def create_app(repository: Take5Repository | None = None) -> FastAPI:
    """Build the API; tests can supply storage without changing any route or rule."""
    database_path = Path(
        os.environ.get(
            "TAKE5_DATABASE_PATH",
            str(Path(__file__).parents[3] / ".data/take5.sqlite3"),
        )
    )
    storage: Take5Repository = (
        repository if repository is not None else SqliteTake5Repository(database_path)
    )
    service = Take5Service(storage, BOOKLET_TEMPLATE)
    app = FastAPI(title="Take 5", version="0.1.0")
    app.include_router(create_router(service))
    return app
