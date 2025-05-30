.PHONY: clean
clean:
	git clean -Xf out/

DATE := $(shell date +%Y.%m.%d)
EXISTING_TAGS := $(shell gh release list --json tagName -q '.[] | .tagName' | grep '^$(DATE)')

.PHONY: create-release
create-release:
	@N=1; \
	while echo "$(EXISTING_TAGS)" | grep -q "^$(DATE).$$$${N}"; do \
	  N=$$(($$N + 1)); \
	done; \
	TAG="$(DATE).$$N"; \
	echo "Creating GitHub release for tag: $$TAG"; \
	gh release create $$TAG --generate-notes
