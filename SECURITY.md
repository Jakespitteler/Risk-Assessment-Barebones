# Security

This repo is public so people can read it, but it is not open source: see [LICENSE](LICENSE).

## Reporting a problem

If you find a security problem, please report it privately: on GitHub, open the **Security** tab and choose
**Report a vulnerability**. Please don't open a public issue or pull request about it. Include what you found,
how to reproduce it, and what someone could do with it. I'll reply as soon as I can.

## What is in scope

- The code in this repo: the back end in `backend/`, the front end in `frontend/` and the scripts.
- The GitHub workflows in `.github/workflows/`.

The app is a proof of concept that runs on a person's own computer. It is not hosted anywhere, so there is no live
site to test. Please don't test against anything except your own copy.

## Secrets and data

The repo holds no keys, passwords or real worker data. AI keys live only in `backend/.env`, which git ignores,
and saved Take 5s stay in `backend/.data/`, which git ignores too. If you think something secret was committed,
report it as above.
