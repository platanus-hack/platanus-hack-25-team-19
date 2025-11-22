.PHONY: help install format lint test deploy clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

format: ## Format code with black and isort
	python -m black .
	python -m isort .

lint: ## Run linters (flake8)
	python -m flake8 .

test: ## Run tests
	python -m pytest

pre-commit: ## Run pre-commit hooks on all files
	python -m pre_commit run --all-files

layer: ## Build Lambda layer dependencies
	cd lambda/layer && \
	rm -rf python && \
	pip install -r requirements.txt -t python/

synth: ## Synthesize CDK stack
	cdk synth

diff: ## Show CDK diff
	cdk diff

deploy: ## Deploy CDK stack
	cdk deploy

destroy: ## Destroy CDK stack
	cdk destroy

clean: ## Clean generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf cdk.out

.DEFAULT_GOAL := help
