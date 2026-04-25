.PHONY: clean
clean:
	git clean -Xf out/

.PHONY: test
test:
	uv run python -m pytest -q

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
