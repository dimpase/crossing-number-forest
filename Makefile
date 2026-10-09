PYTHON ?= python3
PORT ?= 8001
FORESTER_SWITCH ?= 4ary-4tics-forester-5.0
export FORESTER_SWITCH

.PHONY: setup build serve check

setup:
	$(PYTHON) scripts/setup.py

build:
	$(PYTHON) scripts/build.py

serve: build
	@echo "Open http://127.0.0.1:$(PORT)/index/index.html (Ctrl-C to stop)"
	$(PYTHON) -m http.server $(PORT) --bind 127.0.0.1 --directory output

check: build
	$(PYTHON) computations/check_examples.py
	$(PYTHON) computations/check_lean_sources.py
