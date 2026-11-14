---
id: 0016
title: Share the back end's test set-up through conftest.py files
status: review
owner: claude
branch: claude/project-thread-a5tkiz
---

## Goal

Jake asked (2026-11-14) whether `conftest.py` files would make the tests simpler and clearer. They would: the back
end has no fixtures and no `conftest.py`, so each test file builds its own client, repository and sample Take 5.

## Acceptance criteria

- [x] `backend/tests/api/conftest.py` has a `client` fixture: a `TestClient` over `create_app` with a fresh
  SQLite repository in `tmp_path`. It replaces the 13 copies of
  `TestClient(create_app(SqliteTake5Repository(tmp_path / "take5.sqlite3")))` in `test_take5_workflow.py`. Tests
  that need their own repository (for example, reopening the same database) keep building it.
- [x] One shared builder for a sample draft replaces the copies of `_draft()` in `tests/api/` and
  `tests/services/`. The same goes for the hazard builders in `tests/domain/take5/`.
- [x] Each fixture and builder has a docstring that says what it gives, and its name says what it is.
- [x] No test's meaning changes: the same tests, the same assertions, and all checks pass.

## Out of scope

- New tests, and the front end's tests.

## Notes / assumptions

Plain builder functions (for example `sample_draft()`) may read better than fixtures for test data, because a test
can pass arguments to them. Fixtures suit set-up such as the client. Put a builder in a `conftest.py` only if tests
in more than one folder use it; otherwise keep it in the folder's own `conftest.py`.

Best done after 0010 and before 0005, so the tests that 0005 to 0008 add use the shared set-up from the start.

### What was done (claude, 2026-11-14)

- `backend/tests/api/conftest.py` has two fixtures: `repository`, an empty SQLite database in `tmp_path`, and
  `client`, the real app over that same repository. A test that checks what was saved asks for both. 14 of the
  17 tests in `test_take5_workflow.py` that built their own client now use the fixture. The 3 that don't each
  need the database file itself: two reopen the same file with a new repository, and one checks that no file
  was created. The two template tests in `test_take5_routes.py` keep `TestClient(create_app())`, because they
  don't touch a database at all.
- The shared builders are plain functions in `backend/tests/samples.py`, not in a `conftest.py`, because
  pytest's documentation says not to import from a `conftest.py`, and a fixture can't take arguments. Why is in
  `docs/decisions.md`. They are `sample_draft()`, `sample_hazard_draft()`, `sample_uncontrolled_draft()`
  (example 22), `sample_hazard()` and `sample_saved_take5()`, with the `BARRICADE` controls they use. They
  replace two `_draft()` and two "without controls" builders (API and services), the `_hazard()` and `_draft()`
  in `test_draft.py`, the `_hazard()` in `test_take5.py`, the hazard inside `_take5()` in `test_verdict.py`, and
  the `_saved()` copies in `test_fix.py` and `test_sqlite.py`. Local helpers used by one file only, such as
  `_take5()` and `_service()`, stay where they are.
- Assumption: only the made-up names changed. The services tests' draft was a different made-up job ("Example
  maintenance task"), and two domain tests named their hazard "Example hazard" and their control "Barricade the
  hazard". They now use the shared example. No assertion reads those names, and one services test that needs
  the after rating to stay 8 asks for it: `sample_hazard_draft(after=("Possible", "Minor"))`.
- Checked: the same 301 tests are collected before and after (compared by name), and all pass.
- Also wrapped the 121-character Markdown line in `AGENTS.md` left over from task 0017.
