# Convenience commands. Run `make help` to see them.

.PHONY: help install demo prompt eval test lint

help:
	@echo "make install   - install the package (editable) with dev tools"
	@echo "make demo       - validate the EAT profile and run the eval set"
	@echo "make prompt     - print the system prompt rendered from the EAT profile"
	@echo "make eval        - run the evaluation set and report pass/fail"
	@echo "make test        - run the unit tests"
	@echo "make lint        - run ruff"

install:
	pip install -e ".[dev]"

lint:
	ruff check .

demo:
	python3 run.py

prompt:
	python3 run.py prompt

eval:
	python3 run.py eval

test:
	python3 -m unittest discover -s tests -p "test_*.py" -v
