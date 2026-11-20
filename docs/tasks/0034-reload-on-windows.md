---
id: 0034
title: Keep the app running on Windows when back-end code changes
status: review
owner: claude
branch: claude/0034-reload-on-windows
---

## Goal

On Windows, saving a back-end file stopped the whole app without a word, and a change that broke the back end
only showed its error on the next `uv run start.py` (Jake, 2026-11-20). `start.py` now restarts the back end
itself when its code is saved, keeps the front end running, and shows at once why a broken change won't start.

## Acceptance criteria

- [ ] Saving a Python file under `backend/src` restarts only the back end, on Windows as on macOS and Linux.
- [ ] A change that stops the back end starting prints its error and a line saying the app waits for a fix; the
  front end keeps running, and the next save starts the back end again.
- [ ] Ctrl+C still stops everything, as before.
- [ ] Tests cover the restart, the wait for a fix and the change detection.
- [ ] Jake checks it on Windows: save a file, break one, fix it, then Ctrl+C.
- [ ] All checks pass.

## Out of scope

- How errors look once the app runs (task 0028).
- Restarting the front end: Vite reloads by itself, and that works on Windows.

## Notes / assumptions

Jake picked "Fix it here, own PR after #60" on 2026-11-20, after his app stopped when uvicorn reloaded.

The cause, from uvicorn 0.54's own code (`supervisors/basereload.py`, `restart()`): on Windows its reloader
restarts the worker with `os.kill(pid, signal.CTRL_C_EVENT)`. Windows can't send Ctrl+C to one process, so every
program in the terminal gets it, `start.py` included, which took it for the person's Ctrl+C and stopped
everything. On macOS and Linux the reloader stops the worker another way, which is why only Windows was hit.
This can't be run here (no Windows), so Jake's check on Windows is a criterion.

`start.py` now runs uvicorn without `--reload` and looks once a second for a saved, added or removed `.py` file
under `backend/src`, the same files uvicorn watched apart from the tests. No new package: the file times come
from the standard library. An editor that saves two files a second apart restarts the back end twice, which
is harmless.
