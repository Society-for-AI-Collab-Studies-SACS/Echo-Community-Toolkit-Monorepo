install:
	python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -e .

test:
	pytest -q

generate:
	python -m echo_soulcode.live_read --alpha 0.58 --beta 0.39 --gamma 0.63 --out examples/echo_live.json

validate:
	python -m echo_soulcode.validate --file examples/echo_live.json
