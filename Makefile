HTTP_PORT ?= 8080

.PHONY: build
build:
	pip install -U pip
	pip install -r requirements.txt

.PHONY: test
test:
	@PYTHONPATH=. pytest

.PHONY: format
format:
	black .
	isort .

.PHONY: run
run:
	python app/main.py --port $(HTTP_PORT) --verbose
