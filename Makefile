# CreditPulse — developer entry points (implementation-plan.md §3).
PY ?= .venv/bin/python
PIP ?= .venv/bin/pip
PORT ?= 8080
N ?= 400

.PHONY: help venv install data-gen prefit test eval train demo docker-build docker-run clean

help:
	@echo "make install     - create venv and install pinned deps"
	@echo "make prefit      - fit + pickle the scoring engine (instant demo startup)"
	@echo "make data-gen    - generate synthetic cohort into app/data/ (N=$(N))"
	@echo "make test        - run the unit-test suite"
	@echo "make eval        - run the eval harness scorecard"
	@echo "make train       - fit models + print the 6-archetype demo scorecard"
	@echo "make demo        - launch the Streamlit app on PORT=$(PORT)"
	@echo "make docker-build / docker-run - container build + local run"

venv:
	python3 -m venv .venv

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

data-gen:
	$(PY) -m app.data_gen.build_dataset --n $(N)

prefit:
	$(PY) -m app.ml.prefit

test:
	$(PY) -m pytest app/tests app/tracks -q

eval:
	$(PY) -m app.ml.eval.runner

train:
	$(PY) -m app.ml.train

demo: prefit
	$(PY) -m streamlit run app/frontend/main.py --server.port=$(PORT) --server.address=0.0.0.0

docker-build:
	docker build -t creditpulse:local .

docker-run:
	docker run --rm -e PORT=$(PORT) -p $(PORT):$(PORT) creditpulse:local

clean:
	rm -rf app/data/*.csv .pytest_cache **/__pycache__
