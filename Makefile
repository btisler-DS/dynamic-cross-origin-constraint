.PHONY: dev dev-backend dev-frontend test build up down clean

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

dev:
	$(MAKE) -j2 dev-backend dev-frontend

test:
	cd backend && python -m pytest tests/ -v

sim:
	cd backend && python -m simulation.engine --seed 42 --epochs 20

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

clean:
	rm -rf data/*.db data/reports data/weights
	rm -rf frontend/node_modules frontend/dist
	rm -rf backend/__pycache__
