.PHONY: ruff_fix_imports ruff_format ruff_lint clean generate-openapi run_backend run_frontend dev

QA_CHECK_DIR := ./api/ ./tests/
QA_EXCLUDE_DIR := ./notebook/

OPENAPI_JSON := frontend/openapi.json
OPENAPI_TS := frontend/lib/openapi.generated.ts

ruff_fix_imports:
	uv run ruff check --select I --fix $(QA_CHECK_DIR) --exclude $(QA_EXCLUDE_DIR)

ruff_format:
	uv run ruff format $(QA_CHECK_DIR) --exclude $(QA_EXCLUDE_DIR)

ruff_lint:
	uv run ruff check --fix $(QA_CHECK_DIR) --exclude $(QA_EXCLUDE_DIR)
	
clean:
	find . -type f -name "*.DS_Store" -ls -delete
	find . | grep -E "(__pycache__|\.pyc|\.pyo)" | xargs rm -rf
	find . | grep -E ".pytest_cache" | xargs rm -rf
	find . | grep -E ".ipynb_checkpoints" | xargs rm -rf
	rm -rf .coverage*
	rm -f $(OPENAPI_JSON)

generate-openapi:
	uv run python -c "import json; from api.main import app; print(json.dumps(app.openapi(), indent=2))" > $(OPENAPI_JSON)
	cd frontend && pnpm dlx openapi-typescript openapi.json -o lib/openapi.generated.ts
	rm -f $(OPENAPI_JSON)
	@echo "Updated $(OPENAPI_TS)"


run_backend:
	set -a; source .env; set +a; uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 9000

run_frontend:
	cd frontend && pnpm dev

dev:
	@echo "Run 'make run_backend_dev' and 'make run_frontend_dev' in separate terminals"

