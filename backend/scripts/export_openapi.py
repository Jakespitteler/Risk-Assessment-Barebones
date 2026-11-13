"""Write the API description (OpenAPI) to a file.

The front end's TypeScript types are generated from that file, so the two halves of the
app can't drift apart. Usage: `uv run python scripts/export_openapi.py <output path>`.
"""

import json
import sys
from pathlib import Path

from risk_assessment.api.app import create_app


def export_openapi(output_path: Path) -> None:
    """Write the app's OpenAPI description to `output_path` as indented JSON."""
    description = json.dumps(create_app().openapi(), indent=2)
    output_path.write_text(description + "\n", encoding="utf-8")


if __name__ == "__main__":
    export_openapi(Path(sys.argv[1]))
