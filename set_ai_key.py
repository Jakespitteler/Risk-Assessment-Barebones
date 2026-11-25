# /// script
# requires-python = ">=3.13"
# ///
"""Save the AI's key in `backend/.env`, so the app can use the AI (task 0046).

Usage, from the repo root: `uv run set_ai_key.py`, then paste the key when asked.

The key is typed in, not given on the command line, so it stays out of the shell's
history, and it isn't shown as it is pasted. It becomes the `TAKE5_AI_KEY=` line in
`backend/.env`: the file is made if there is none, the line is replaced if there is
one, and every other line is kept. Git ignores `.env`, so the key never leaves this
computer. The key is never printed.
"""

import getpass
import sys
from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parent
SETTINGS_FILE: Path = REPO_ROOT / "backend" / ".env"
KEY_SETTING: str = "TAKE5_AI_KEY"


def is_key_line(line: str) -> bool:
    """Tell whether a settings line sets the AI key, with or without a value.

    Args:
        line: One line of the settings file.

    Returns:
        True for a line such as `TAKE5_AI_KEY=...`; False for a comment or another
        setting.
    """
    setting_name: str = line.partition("=")[0].strip()
    return "=" in line and setting_name == KEY_SETTING


def with_key(lines: list[str], key: str) -> list[str]:
    """Give the settings lines with the AI key set to the new key.

    Args:
        lines: The settings file's lines, without their line endings.
        key: The new key.

    Returns:
        The same lines, with every key line replaced by one new key line where the
        first one was, or the new key line added at the end when there was none.
    """
    key_line: str = f"{KEY_SETTING}={key}"
    new_lines: list[str] = []
    for line in lines:
        if not is_key_line(line):
            new_lines.append(line)
        elif key_line not in new_lines:
            new_lines.append(key_line)
    if key_line not in new_lines:
        new_lines.append(key_line)
    return new_lines


def save_key(settings_file: Path, key: str) -> None:
    """Write the key into the settings file, keeping its other lines.

    Args:
        settings_file: The `.env` file. It is made if it doesn't exist.
        key: The key to save.
    """
    old_lines: list[str] = (
        # A file saved on Windows may start with a byte order mark.
        settings_file.read_text(encoding="utf-8-sig").splitlines()
        if settings_file.is_file()
        else []
    )
    new_text: str = "\n".join(with_key(old_lines, key)) + "\n"
    settings_file.write_text(new_text, encoding="utf-8")


def main() -> int:
    """Ask for the key and save it.

    Returns:
        0 when the key was saved, 1 when nothing was.
    """
    try:
        key: str = getpass.getpass(
            "Paste the AI key and press Enter (it won't show as you paste): ",
        ).strip()
    except (KeyboardInterrupt, EOFError):
        print("\nNothing was saved.")
        return 1
    if not key:
        print("No key was pasted, so nothing was saved.")
        return 1
    save_key(SETTINGS_FILE, key)
    print("Saved the key in backend/.env. Start the app again: uv run start.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
