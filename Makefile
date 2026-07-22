.PHONY: clean ruff_fix_imports ruff_format ruff_lint

# --- QA ---

QA_CHECK_DIR := ./api/ ./tests/
QA_EXCLUDE_DIR := ./notebook/

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

run_backend:
	set -a; source .env; set +a; uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

run_frontend:
	cd frontend && pnpm dev

dev:
	@echo "Run 'make run_backend_dev' and 'make run_frontend_dev' in separate terminals"

