.PHONY: all embed-echo-key verify mrp-validate clean g2v g2v-venv g2v-install g2v-tests g2v-examples

all: embed-echo-key verify mrp-validate

embed-echo-key:
	python3 scripts/embed_golden_echo_key.py

verify:
	python3 verify_updated_system.py

mrp-validate:
	python3 scripts/mrp_validate_rgb.py

clean:
	rm -rf artifacts
	rm -rf examples/data
	rm -f demo_cover.png demo_stego.png rt_cover.png rt_stego.png
	rm -f assets/images/mrp_stego_out.png
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache

g2v-venv:
	python3 -m venv .venv || true

g2v-install: g2v-venv
	@if [ -f .venv/bin/activate ]; then \
		. .venv/bin/activate && python -m pip install -U pip && python -m pip install -e . ; \
	else \
		python3 -m pip install --user --break-system-packages --no-build-isolation -e . || true ; \
	fi

g2v-tests:
	@if [ -f .venv/bin/activate ]; then \
		. .venv/bin/activate && python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('pytest') else 1)" >/dev/null 2>&1 && pytest -q tests/test_volume.py tests/test_fft_codec.py || (. .venv/bin/activate && python scripts/g2v_minimal_checks.py) ; \
	else \
		python3 -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('pytest') else 1)" >/dev/null 2>&1 && pytest -q tests/test_volume.py tests/test_fft_codec.py || python3 scripts/g2v_minimal_checks.py ; \
	fi

g2v-examples:
	@if [ -f .venv/bin/activate ]; then \
		. .venv/bin/activate && python examples/demo_stack_and_project.py ; \
	else \
		python3 examples/demo_stack_and_project.py ; \
	fi

g2v: g2v-install g2v-tests g2v-examples
