SHELL := /bin/bash

.DEFAULT_GOAL := help

PYTHON ?= python3
PIP ?= pip3
COMPOSE ?= docker compose
APP_HOST ?= 0.0.0.0
APP_PORT ?= 8080
CELERY_LOG_LEVEL ?= info
CELERY_CONCURRENCY ?= 1

COMPOSE_FILES := -f docker-compose.yml
CI_COMPOSE_FILES := -f docker-compose.yml -f docker-compose.ci.yml

.PHONY: help install install-backend install-frontend run-api run-worker run-beat \
	run-flower test test-unit test-integration test-e2e test-collect check \
	compose-up compose-down compose-restart compose-logs compose-ps \
	compose-up-ci compose-down-ci ci-smoke templates-clone clean

help: ## Show available commands
	@grep -E '^[a-zA-Z0-9_.-]+:.*## ' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*## "}; {printf "%-22s %s\n", $$1, $$2}'

install: install-backend ## Install backend dependencies

install-backend: ## Install backend Python dependencies
	$(PIP) install -r requirements.txt

install-frontend: ## Install frontend dependencies (pnpm required)
	pnpm --dir frontend install

run-api: ## Run FastAPI locally with reload on port APP_PORT (default: 8080)
	$(PYTHON) -m uvicorn app.main:app --reload --host $(APP_HOST) --port $(APP_PORT)

run-worker: ## Run Celery worker locally
	PYTHONPATH=app celery -A celery_config:celery_app worker --loglevel=$(CELERY_LOG_LEVEL) --concurrency=$(CELERY_CONCURRENCY)

run-beat: ## Run Celery beat locally
	PYTHONPATH=app celery -A celery_config:celery_app beat --loglevel=$(CELERY_LOG_LEVEL)

run-flower: ## Run Flower locally (requires Redis)
	PYTHONPATH=app celery -A celery_config:celery_app flower --port=5555

test: ## Run all tests
	pytest tests

test-unit: ## Run tests excluding integration/e2e markers
	pytest -m "not integration and not e2e" tests

test-integration: ## Run integration tests
	pytest -m integration tests

test-e2e: ## Run end-to-end tests
	pytest -m e2e tests

test-collect: ## Validate pytest collection
	pytest --collect-only tests

check: ## Compile Python sources and validate test discovery
	$(PYTHON) -m compileall app tests
	$(MAKE) test-collect

compose-up: ## Start full docker compose stack
	$(COMPOSE) $(COMPOSE_FILES) up -d

compose-down: ## Stop full docker compose stack
	$(COMPOSE) $(COMPOSE_FILES) down

compose-restart: ## Restart full docker compose stack
	$(COMPOSE) $(COMPOSE_FILES) restart

compose-logs: ## Tail logs for full docker compose stack
	$(COMPOSE) $(COMPOSE_FILES) logs -f

compose-ps: ## Show docker compose service status
	$(COMPOSE) $(COMPOSE_FILES) ps

compose-up-ci: ## Start CI subset (redis, celery_worker, nuclei-api)
	$(COMPOSE) $(CI_COMPOSE_FILES) up -d redis celery_worker nuclei-api

compose-down-ci: ## Stop CI subset and remove volumes
	$(COMPOSE) $(CI_COMPOSE_FILES) down -v

ci-smoke: compose-up-ci ## Run smoke checks against local CI subset
	@bash -c 'for i in {1..60}; do \
		curl -fsS http://localhost:8000/ >/dev/null && exit 0; \
		sleep 2; \
	done; \
	echo "API did not become ready in time"; \
	$(COMPOSE) $(CI_COMPOSE_FILES) logs nuclei-api; \
	exit 1'
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install requests
	$(PYTHON) - <<'PY'
		import time
		import requests
		
		base_url = "http://localhost:8000"
		ping = requests.get(f"{base_url}/", timeout=30)
		ping.raise_for_status()
		assert ping.json().get("ping") == "pong!"
		
		invalid = requests.post(
		    f"{base_url}/nuclei/scan",
		    json={"target": "not-a-valid-target", "templates": ["cves/"]},
		    timeout=30,
		)
		assert invalid.status_code == 400, invalid.text
		
		scan = requests.post(
		    f"{base_url}/nuclei/scan",
		    json={"target": "example.com", "templates": ["http/"]},
		    timeout=60,
		)
		scan.raise_for_status()
		task_id = scan.json().get("task_id")
		assert task_id, scan.text
		
		final_status = None
		for _ in range(90):
		    status = requests.get(f"{base_url}/nuclei/task/{task_id}", timeout=30)
		    status.raise_for_status()
		    payload = status.json()
		    final_status = payload.get("status")
		    if final_status in {"SUCCESS", "FAILURE"}:
		        break
		    time.sleep(2)
		
		assert final_status in {"SUCCESS", "FAILURE"}, f"task stuck with status={final_status}"
		print(f"Smoke checks passed; task={task_id} status={final_status}")
	PY

templates-clone: ## Clone nuclei templates if not present
	@if [ -d nuclei-templates/.git ]; then \
		echo "nuclei-templates already exists"; \
	else \
		git clone https://github.com/projectdiscovery/nuclei-templates.git; \
	fi

clean: ## Remove Python cache artifacts
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
