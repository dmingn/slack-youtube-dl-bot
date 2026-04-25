.PHONY: clean
clean:
	git clean -Xf out/

.PHONY: fmt
fmt:
	uv run ruff format .
	uv run ruff check --fix .

.PHONY: lint
lint:
	uv run ruff format --check .
	uv run ruff check .

.PHONY: typecheck
typecheck:
	uv run mypy .

.PHONY: test
test:
	uv run python -m pytest -q

.PHONY: check
check: lint typecheck test

DATE := $(shell date +%Y.%m.%d)
EXISTING_TAGS := $(shell git tag -l "$(DATE).*")

.PHONY: create-release
create-release:
	@N=1; \
	while echo "$(EXISTING_TAGS)" | grep -q -x "$(DATE).$${N}"; do \
	  N=$$(($$N + 1)); \
	done; \
	TAG="$(DATE).$${N}"; \
	echo "Creating GitHub release for tag: $${TAG}"; \
	gh release create $${TAG} --generate-notes
