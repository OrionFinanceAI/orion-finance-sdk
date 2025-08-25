.PHONY: uv-download
uv-download:
	@command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh

.PHONY: venv
venv:
	rm -rf .venv build dist *.egg-info
	rm -rf abis/
	uv venv

.PHONY: install
install:
	uv pip install -e .
	cd js && npm install && npm run build
	./scripts/build_js.sh

.PHONY: install-dev
install-dev:
	uv pip install -e ."[dev]"
	uv run pre-commit install

.PHONY: codestyle
codestyle:
	uv run ruff check --select I --fix ./
	uv run ruff format ./
	cd js && npm run prettier

.PHONY: check-codestyle
check-codestyle:
	uv run ruff check --select I --fix --exit-non-zero-on-fix ./
	uv run ruff format --diff ./
	cd js && npm run prettier:check

.PHONY: docs
docs:
	uv run pydocstyle

.PHONY: test
test:
	uv run pytest -c pyproject.toml tests/
