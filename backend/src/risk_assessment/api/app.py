"""Builds the web app.

This is the one place that decides which real pieces are plugged in.
"""

from fastapi import FastAPI

from risk_assessment.api import take5_routes


def create_app() -> FastAPI:
    """Build the FastAPI app with every route attached.

    Returns:
        The app, ready for uvicorn to serve or for a test client to call.
    """
    app: FastAPI = FastAPI(title="Take 5", version="0.1.0")
    app.include_router(take5_routes.router)
    return app
