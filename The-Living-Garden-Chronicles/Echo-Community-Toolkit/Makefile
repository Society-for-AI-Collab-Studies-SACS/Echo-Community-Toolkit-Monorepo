MONO_PY := echo-soulcode-architecture

.PHONY: help python-setup emit-schema types bundle validate node-integrate all

help:
	@echo "Targets:"
	@echo "  python-setup   - create venv + install python package"
	@echo "  emit-schema    - emit soulcode JSON schemas (python)"
	@echo "  types          - generate TS types from schemas"
	@echo "  bundle         - generate soulcode bundle via python"
	@echo "  validate       - validate bundle via AJV"
	@echo "  node-integrate - run Node integration (HTML updates)"
	@echo "  all            - setup -> emit -> types -> bundle -> validate -> integrate"

python-setup:
	@$(MAKE) -C $(MONO_PY) install

emit-schema:
	npm run soulcode:emit-schema

types:
	npm run soulcode:types

bundle:
	npm run soulcode:bundle

validate:
	npm run soulcode:validate

node-integrate:
	npm run integrate

all: python-setup emit-schema types bundle validate node-integrate
	@echo "Monorepo integration complete."
PYTEST?=python3 -m pytest -q

.PHONY: test validate ui-test

test:
	$(PYTEST)

validate:
	python3 final_validation.py

ui-test:
	cd lambda-vite && npm ci && npm test --silent
