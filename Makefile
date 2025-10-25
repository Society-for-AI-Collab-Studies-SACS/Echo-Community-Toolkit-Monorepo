.PHONY: g2v-sync-pull g2v-sync-push g2v-sync-verify

g2v-sync-pull:
	bash scripts/g2v_sync.sh --pull

g2v-sync-push:
	bash scripts/g2v_sync.sh --push

g2v-sync-verify:
	bash scripts/g2v_sync.sh --verify

.PHONY: setup test run-example fmt

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -e . pytest

test:
	. .venv/bin/activate && pytest

run-example:
	. .venv/bin/activate && python examples/demo_stack_and_project.py

fmt:
	@echo "(no formatter wired; add ruff/black if desired)"
