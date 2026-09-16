.PHONY: up down build logs shared-install index synth-data test-agent1 test-agent2 test-agent3 test-agent4 test-all

up:
	docker-compose up --build

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

shared-install:
	pip install -e shared

index:
	cd services/agent3-retrieval && python -m app.indexing.build_index

synth-data:
	python data/scripts/generate_synthetic_returns.py

test-agent1:
	cd services/agent1-intake && pytest tests/ -v

test-agent2:
	cd services/agent2-rootcause && pytest tests/ -v

test-agent3:
	cd services/agent3-retrieval && pytest tests/ -v

test-agent4:
	cd services/agent4-decision && pytest tests/ -v

test-all: test-agent1 test-agent2 test-agent3 test-agent4
