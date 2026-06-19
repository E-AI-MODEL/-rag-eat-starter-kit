# Convenience commands. Run `make help` to see them.

.PHONY: help install demo prompt eval test

help:
	@echo "make install   - install dependencies (PyYAML)"
	@echo "make demo       - validate the EAT profile and run the eval set"
	@echo "make prompt     - print the system prompt rendered from the EAT profile"
	@echo "make eval        - run the evaluation set and report pass/fail"
	@echo "make test        - run the unit tests"

install:
	pip install -r requirements.txt

demo:
	python3 run.py

prompt:
	python3 run.py prompt

eval:
	python3 run.py eval

test:
	python3 -m unittest discover -s tests -p "test_*.py" -v
