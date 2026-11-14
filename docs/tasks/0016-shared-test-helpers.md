---
id: 0016
title: Share the back end's test set-up through conftest.py files
status: in-progress
owner: claude
branch: claude/project-thread-a5tkiz
---

## Goal

Jake asked (2026-11-14) whether `conftest.py` files would make the tests simpler and clearer. They would: the back
end has no fixtures and no `conftest.py`, so each test file builds its own client, repository and sample Take 5.

## Acceptance criteria

- [ ] `backend/tests/api/conftest.py` has a `client` fixture: a `TestClient` over `create_app` with a fresh
  SQLite repository in `tmp_path`. It replaces the 13 copies of
  `TestClient(create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3")))` in `test_take5_workflow.py`. Tests
  that need their own repository (for example, reopening the same database) keep building it.
- [ ] One shared builder for a sample draft replaces the copies of `_draft()` in `tests/api/` and
  `tests/services/`. The same goes for the hazard builders in `tests/domain/take5/`.
- [ ] Each fixture and builder has a docstring that says what it gives, and its name says what it is.
- [ ] No test's meaning changes: the same tests, the same assertions, and all checks pass.

## Out of scope

- New tests, and the front end's tests.

## Notes / assumptions

Plain builder functions (for example `sample_draft()`) may read better than fixtures for test data, because a test
can pass arguments to them. Fixtures suit set-up such as the client. Put a builder in a `conftest.py` only if tests
in more than one folder use it; otherwise keep it in the folder's own `conftest.py`.

Best done after 0010 and before 0005, so the tests that 0005 to 0008 add use the shared set-up from the start.
