PYTHON ?= python3
PORT ?= 8001
FORESTER_SWITCH ?= 4ary-4tics-forester-5.0
FOREST_URL ?=
export FORESTER_SWITCH FOREST_URL

.PHONY: setup build serve check check-local

setup:
	$(PYTHON) scripts/setup.py

build:
	$(PYTHON) scripts/build.py

serve: build
	@echo "Open http://127.0.0.1:$(PORT)/index/index.html (Ctrl-C to stop)"
	$(PYTHON) -m http.server $(PORT) --bind 127.0.0.1 --directory output

check: build check-local

# Source and exact checks that do not require the Forester rendering toolchain.
check-local:
	$(PYTHON) scripts/check.py --sources
	$(PYTHON) computations/check_examples.py
	$(PYTHON) computations/check_lean_sources.py
	$(PYTHON) computations/check_subspace_slack.py
	$(PYTHON) -m unittest discover -s tests -v
