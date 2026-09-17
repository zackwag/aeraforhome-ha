# AGENTS.md

## Project overview

Home Assistant custom integration (HACS) for Aera for Home smart fragrance diffusers. Python, built on the Home Assistant custom component framework, using the `aeraforhome` PyPI client library.

## Setup

```sh
pip install -r requirements_test.txt
```

## Build / Run

N/A — this is a Home Assistant custom component, not a standalone app. It's installed into a running Home Assistant instance (via HACS or by copying `custom_components/aeraforhome/` into HA's config directory).

## Test

```sh
pytest
```

Config: `pyproject.toml` (`testpaths = ["tests"]`, `asyncio_mode = "auto"`). Uses `pytest-homeassistant-custom-component` to simulate a Home Assistant environment.

CI also runs `hassfest` and HACS validation (`.github/workflows/validate.yml`) against `hacs.json` and the component manifest.

## Repository structure

- `custom_components/aeraforhome/` — the integration itself (config flow, entities, coordinator)
- `tests/` — pytest suite
- `blueprints/` — Home Assistant automation blueprints shipped with the integration
- `hacs.json` — HACS metadata

## Commit and PR conventions

- Commit messages and PR titles must follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `ci:`, `build:`, `perf:`, `style:`, `revert:`), optionally with a scope, e.g. `fix(api): handle null response`.
- This repo squash-merges pull requests only; the PR title becomes the final commit message on `main`.
- A "Conventional Commits" CI check enforces this on both PR titles and direct-push commit messages.
- Branch protection on `main`: no force-pushes, no branch deletion, required status checks must pass.
