# =============================================================================
# Makefile for ADK 2.0 Agent-to-Agent (A2A) Boilerplate
# =============================================================================

.DEFAULT_GOAL := help
SHELL := /usr/bin/env bash

# Colors for terminal output
COLOR_RESET  := \033[0m
COLOR_INFO   := \033[36m
COLOR_SUCCESS:= \033[32m
COLOR_WARN   := \033[33m

.PHONY: help install run serve info todoist-auth ge-manifest test lint format check report docker-build docker-up docker-down deploy-cloud-run deploy-ge register-ge-a2a clean

## 📋 Help & Overview
help: ## Show this help message
	@echo -e "$(COLOR_INFO)ADK 2.0 A2A Boilerplate - Developer CLI$(COLOR_RESET)"
	@echo -e "Usage: make [target]"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(COLOR_SUCCESS)%-20s$(COLOR_RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

## 📦 Setup & Dependencies
install: ## Install all dependencies via uv (with A2A and GCP extras)
	@echo -e "$(COLOR_INFO)Installing dependencies with uv...$(COLOR_RESET)"
	uv sync --all-extras

## 🚀 Local Execution
run: ## Run local orchestrator goal (default: Tokyo vs Paris weather)
	@echo -e "$(COLOR_INFO)Running orchestrator goal...$(COLOR_RESET)"
	uv run python main.py run "Compare the temperature difference between Tokyo and Paris"

serve: ## Start A2A micro-agent server on port 8080 (to_a2a mode)
	@echo -e "$(COLOR_INFO)Starting A2A micro-agent server on http://localhost:8080...$(COLOR_RESET)"
	uv run python main.py serve --host 0.0.0.0 --port 8080 --mode adk

info: ## Display A2A Agent Card and environment settings
	@uv run python main.py info

todoist-auth: ## Display Todoist OAuth2 login URL and instructions
	@uv run python main.py todoist-auth

ge-manifest: ## Display Gemini Enterprise A2A registration manifest & payloads
	@uv run python main.py ge-manifest

## 🧪 Testing & Code Quality
test: ## Run automated pytest suite
	@echo -e "$(COLOR_INFO)Running Pytest suite...$(COLOR_RESET)"
	uv run pytest

lint: ## Run Ruff linter and strict Mypy type checker
	@echo -e "$(COLOR_INFO)Checking code with Ruff and Mypy...$(COLOR_RESET)"
	uv run ruff check .
	uv run mypy src/ tests/

format: ## Auto-format code with Ruff
	@echo -e "$(COLOR_INFO)Formatting code with Ruff...$(COLOR_RESET)"
	uv run ruff format .

check: lint test ## Run both linting and testing in sequence

report: ## Run lint-and-report.sh to generate AI clean code report
	@echo -e "$(COLOR_INFO)Generating Lint → AI report...$(COLOR_RESET)"
	./scripts/lint-and-report.sh

## 🐳 Docker & Containers
docker-build: ## Build the production Docker image locally
	@echo -e "$(COLOR_INFO)Building Docker image...$(COLOR_RESET)"
	./scripts/deploy.sh docker

docker-up: ## Start local multi-agent environment with docker compose
	@echo -e "$(COLOR_INFO)Starting docker compose services...$(COLOR_RESET)"
	docker compose up -d

docker-down: ## Stop local docker compose services
	@echo -e "$(COLOR_INFO)Stopping docker compose services...$(COLOR_RESET)"
	docker compose down

## ☁️ Cloud Deployment & Gemini Enterprise Registration
deploy-cloud-run: ## Deploy A2A service to Google Cloud Run (requires GOOGLE_CLOUD_PROJECT)
	@echo -e "$(COLOR_INFO)Deploying to Google Cloud Run...$(COLOR_RESET)"
	./scripts/deploy.sh cloud_run

deploy-ge: ## Deploy to Vertex AI Agent Engine (GE) (requires GOOGLE_CLOUD_PROJECT)
	@echo -e "$(COLOR_INFO)Deploying to Vertex AI Agent Engine (GE)...$(COLOR_RESET)"
	./scripts/deploy.sh agent_engine

register-ge-a2a: ## Register A2A Agent & Todoist OAuth in Gemini Enterprise
	@echo -e "$(COLOR_INFO)Registering A2A Agent in Gemini Enterprise...$(COLOR_RESET)"
	./scripts/register-ge-a2a.sh

## 🧹 Maintenance & Cleanup
clean: ## Remove temporary cache and test artifacts
	@echo -e "$(COLOR_INFO)Cleaning temporary files and caches...$(COLOR_RESET)"
	rm -rf .pytest_cache .mypy_cache .ruff_cache __pycache__ build/ dist/ *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo -e "$(COLOR_SUCCESS)Clean complete.$(COLOR_RESET)"
