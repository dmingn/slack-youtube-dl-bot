.PHONY: clean
clean:
	git clean -Xf out/

.PHONY: docker-smoke
docker-smoke:
	@if [ -z "$(IMAGE)" ]; then echo "ERROR: IMAGE is required (e.g. IMAGE=slack-youtube-dl-bot:dev)" >&2; exit 1; fi
	@set -e; \
	platform_flag="$(if $(PLATFORM),--platform $(PLATFORM),)"; \
	echo "Smoke testing $(IMAGE) ($(if $(PLATFORM),$(PLATFORM),native))"; \
	docker run --rm $$platform_flag --entrypoint python "$(IMAGE)" -m slack_youtube_dl_bot --help >/dev/null; \
	docker run --rm $$platform_flag --entrypoint ffmpeg "$(IMAGE)" -version >/dev/null; \
	echo "OK"

.PHONY: docker-build-smoke
docker-build-smoke:
	@if [ -z "$(PLATFORM)" ]; then echo "ERROR: PLATFORM is required (e.g. PLATFORM=linux/amd64)" >&2; exit 1; fi
	@set -e; \
	tag="$(if $(TAG),$(TAG),local-smoke)"; \
	echo "Building $$tag for $(PLATFORM)"; \
	docker buildx build --load --platform "$(PLATFORM)" -t "$$tag" .; \
	$(MAKE) docker-smoke IMAGE="$$tag" PLATFORM="$(PLATFORM)"

.PHONY: docker-build-smoke-all
docker-build-smoke-all:
	$(MAKE) docker-build-smoke TAG="$${TAG:-local-smoke}-amd64" PLATFORM=linux/amd64
	$(MAKE) docker-build-smoke TAG="$${TAG:-local-smoke}-arm64" PLATFORM=linux/arm64

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
