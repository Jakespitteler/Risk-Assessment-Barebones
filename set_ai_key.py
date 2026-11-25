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

import codecs
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


def is_usable_key(key: str) -> bool:
    """Tell whether a pasted key can be saved as one settings line.

    No provider's key has a space or a hidden character in it, and one would break
    the line, so such a paste is a mistake (such as a Ctrl+V the terminal didn't paste).

    Args:
        key: The pasted key, without spaces at its ends.

    Returns:
        True when the key is not empty and every character is visible.
    """
    return key != "" and all(
        character.isprintable() and not character.isspace() for character in key
    )


def read_settings_text(settings_file: Path) -> str:
    """Read the settings file's text, however Windows saved it.

    Args:
        settings_file: The `.env` file, which exists.

    Returns:
        The file's text.

    Raises:
        UnicodeDecodeError: When the file is neither UTF-8 nor UTF-16.
    """
    file_bytes: bytes = settings_file.read_bytes()
    # PowerShell's `>` saves UTF-16, which the app can't read; saving again fixes it.
    if file_bytes.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return file_bytes.decode("utf-16")
    # A file saved on Windows may start with a byte order mark.
    return file_bytes.decode("utf-8-sig")


def save_key(settings_file: Path, key: str) -> None:
    """Write the key into the settings file, keeping its other lines.

    The file is always written as UTF-8, which the app reads.

    Args:
        settings_file: The `.env` file. It is made if it doesn't exist.
        key: The key to save.

    Raises:
        UnicodeDecodeError: When the existing file is neither UTF-8 nor UTF-16.
    """
    old_lines: list[str] = (
        read_settings_text(settings_file).splitlines()
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
    if not is_usable_key(key):
        print(
            "That has a space or a hidden character in it, so it isn't a key and"
            " nothing was saved. Copy the key again and paste it.",
        )
        return 1
    try:
        save_key(SETTINGS_FILE, key)
    except UnicodeDecodeError:
        print(
            "backend/.env isn't saved as text this command can read, so nothing was"
            " saved. Save it as UTF-8 in VS Code, or delete it, and run this again.",
        )
        return 1
    print("Saved the key in backend/.env. Start the app again: uv run start.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
