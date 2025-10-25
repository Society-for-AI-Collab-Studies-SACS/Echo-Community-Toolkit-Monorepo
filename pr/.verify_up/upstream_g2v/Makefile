.PHONY: help ci-python venv deps lint test proto clean install example-demo

VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

help:
	@echo "Targets:"
	@echo "  make ci-python   # run local python CI workflow"
	@echo "  make venv        # create virtualenv"
	@echo "  make deps        # install deps + dev tools"
	@echo "  make install     # pip install -e . into venv"
	@echo "  make proto       # generate protobufs (if present)"
	@echo "  make lint        # flake8 agents/"
	@echo "  make test        # pytest"
	@echo "  make example-demo# run examples/demo_stack_and_project.py"
	@echo "  make clean       # remove venv and caches"

ci-python:
	scripts/python_ci_local.sh

venv:
	python3 -m venv $(VENV)

deps: venv
	$(PIP) install --upgrade pip
	@if [ -f requirements.txt ]; then \
	  $(PIP) install -r requirements.txt; \
	fi
	$(PIP) install grpcio grpcio-tools websockets flake8 pytest

install: venv
	$(PIP) install -U pip
	$(PIP) install -e .

proto:
	@if [ -f protos/agents.proto ]; then \
	  $(PY) -m grpc_tools.protoc -Iprotos --python_out=protos --grpc_python_out=protos protos/agents.proto; \
	  $(PY) - <<'PY' ; \
from pathlib import Path; \
p = Path('protos/agents_pb2_grpc.py'); \
\
if p.exists(): \
    t = p.read_text(); \
    t2 = t.replace('import agents_pb2 as agents__pb2', 'from . import agents_pb2 as agents__pb2'); \
    \
    if t2 != t: \
        p.write_text(t2); \
print('protos OK'); \
PY \
	else \
	  echo "No protos/agents.proto found; skipping"; \
	fi

lint:
	@if [ -d agents ]; then \
	  $(VENV)/bin/flake8 agents; \
	else \
	  echo "No agents directory; skipping flake8"; \
	fi

test:
	@if [ -d tests ] || ls -1 test_*.py tests/test_*.py >/dev/null 2>&1; then \
	  $(VENV)/bin/pytest -q; \
	else \
	  echo "No tests detected; skipping pytest"; \
	fi

example-demo:
	$(VENV)/bin/python examples/demo_stack_and_project.py

clean:
	rm -rf $(VENV) .pytest_cache **/__pycache__
