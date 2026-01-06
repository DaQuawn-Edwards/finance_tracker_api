# =========================
# Project configuration
# =========================
PROJECT_NAME = finance_tracker_api
CONDA_ENV = fin_tracker
PYTHON = python
UVICORN = uvicorn
APP = app.main:app
HOST = localhost
PORT = 8000

# =========================
# Conda environment
# =========================
create:
	conda env create -f environment.yml

remove:
	conda env remove -n $(CONDA_ENV)

activate:
	@echo "Run: conda activate $(CONDA_ENV)"

# =========================
# Dependencies
# =========================
install:
	conda activate $(CONDA_ENV) && pip install -r requirements.txt

# =========================
# Database
# =========================
db-check:
	psql "postgresql://ingest:ingest@localhost:5432/ingest_db" -c "SELECT 1;"

# =========================
# Run application
# =========================
run:
	$(UVICORN) $(APP) --reload --host $(HOST) --port $(PORT)

run-prod:
	$(UVICORN) $(APP) --host $(HOST) --port $(PORT)

# =========================
# Development helpers
# =========================
health:
	curl http://$(HOST):$(PORT)/health

docs:
	@echo "Swagger UI: http://$(HOST):$(PORT)/docs"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# =========================
# Meta
# =========================
help:
	@echo ""
	@echo "Available commands:"
	@echo "  make create-env   - Create conda environment from environment.yml"
	@echo "  make remove-env   - Remove conda environment"
	@echo "  make activate     - Show how to activate env"
	@echo "  make install      - Install dependencies"
	@echo "  make run          - Run FastAPI (dev, reload)"
	@echo "  make run-prod     - Run FastAPI (prod)"
	@echo "  make db-check     - Verify PostgreSQL connection"
	@echo "  make health       - Call /health endpoint"
	@echo "  make docs         - Print Swagger UI URL"
	@echo "  make clean        - Remove Python cache files"
	@echo ""
