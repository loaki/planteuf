COMPOSE_FILE=docker/docker-compose-tests.yml
COMPOSE_BINARY=docker-compose
ifeq (, $(shell which docker-compose))
COMPOSE_BINARY=docker compose
endif
COMPOSE_COMMAND=${COMPOSE_BINARY} --env-file .env -f '${COMPOSE_FILE}'
CI_COMMIT_REF_SLUG ?= latest

SRCS := planteuf
MYPY_SRCS := planteuf

.PHONY: help
help: ## show this help
	@grep -E '^[a-zA-Z1-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-30s - %s\n", $$1, $$2}'

.PHONY: install-hooks
install-hooks: ## Install git hooks
	@poetry run pre-commit install

.PHONY: uninstall-hooks
uninstall-hooks: ## Install git hooks
	@poetry run pre-commit uninstall

.PHONY: envvars
envvars: ## Regenerate ENVVARS files
	@./scripts/generate_envvars.sh

.PHONY: lint flake8
lint: ## check code violations using flake8
	@echo >&2 Linting with flake8...
	@poetry run flake8 \
		$(SRCS)
flake8: lint

.PHONY: format
format: ## format source code using isort/black
	@echo >&2 Formatting with black...
	@poetry run isort \
		$(SRCS)
	@poetry run black \
		$(SRCS)

.PHONY: format-check
format-check: ## check source code formatting using isort/black
	@poetry run isort --check \
		$(SRCS)
	@poetry run black --check \
		$(SRCS)

.PHONY: check
check: ## poetry checks
	@poetry check

.PHONY: typing mypy
typing: ## check typing using mypy
	@echo >&2 Checking types with mypy...
	@poetry run dmypy run $(MYPY_SRCS)
mypy: typing
