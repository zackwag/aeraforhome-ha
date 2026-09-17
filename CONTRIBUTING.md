# Contributing to aeraforhome-ha

Thanks for your interest in improving this Home Assistant integration for Aera for Home smart fragrance diffusers.

## Getting started

```sh
git clone https://github.com/zackwag/aeraforhome-ha.git
cd aeraforhome-ha
pip install -r requirements_test.txt
```

## Development

The integration lives in `custom_components/aeraforhome/`. Tests live in `tests/` and use `pytest` with `pytest-homeassistant-custom-component`:

```sh
pytest
```

CI also runs HACS and Home Assistant `hassfest` validation on every push (`.github/workflows/validate.yml`) — make sure `hacs.json` and the integration manifest stay valid.

## Commit messages and pull requests

This repo uses [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`, etc.). Pull requests are squash-merged, and the **PR title** becomes the commit on `main` — so PR titles must follow this format. This is enforced automatically by the "Conventional Commits" check.

Direct pushes to `main` are allowed but must also use a Conventional Commits-formatted commit message (validated by the same check).

## Opening a pull request

1. Fork the repo and create a branch off `main`.
2. Make your changes.
3. Open a pull request with a Conventional Commits-formatted title.
4. Wait for CI to pass — required checks must be green before merge.

## Reporting issues

Use [GitHub Issues](../../issues) for bugs and feature requests.
