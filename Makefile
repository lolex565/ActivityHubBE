up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f backend

db:
	docker exec -it activityhub-db psql -U activityhub -d activityhub_db

backend:
	uvicorn app.main:app --reload

freeze:
	pip freeze > requirements.txt
