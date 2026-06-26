# Convenience commands. Run `make help` to see them.

.PHONY: help install demo prompt eval test lint build check release-check

help:
	@echo "make install       - install the package (editable) with dev, web and LLM extras"
	@echo "make demo          - validate the EAT profile and run the eval set"
	@echo "make prompt        - print the system prompt rendered from the EAT profile"
	@echo "make eval          - run the evaluation set and report pass/fail"
	@echo "make test          - run the unit tests"
	@echo "make lint          - run ruff"
	@echo "make build         - build source and wheel distributions"
	@echo "make check         - run the full local quality gate"
	@echo "make release-check - run the pre-release quality gate"

install:
	pip install -e ".[dev,web,anthropic]"

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

build:
	python3 -m build

check: lint demo test build
	python3 -m compileall run.py web_app.py examples src tests

release-check: check
