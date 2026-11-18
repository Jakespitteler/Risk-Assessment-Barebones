"""Set-up shared by every back-end test."""

import pytest

REAL_AI_MARKER: str = "real_ai"


@pytest.fixture(autouse=True)
def no_ai_key_unless_asked(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hide any AI key on this computer, so no test calls a real AI by accident.

    An empty `TAKE5_AI_KEY` wins over a key in `backend/.env`. Only a test marked
    `real_ai` sees the real key.

    Args:
        request: The test being run, to read its markers.
        monkeypatch: pytest's tool for changing the environment for one test.
    """
    if request.node.get_closest_marker(REAL_AI_MARKER) is None:
        monkeypatch.setenv("TAKE5_AI_KEY", "")
