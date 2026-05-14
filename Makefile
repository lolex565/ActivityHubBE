up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f backend

db:
	docker exec -it activityhub-db psql -U activityhub -d activityhub_db

schema_dump:
	docker exec -it activityhub-db pg_dump -U activityhub -d activityhub_db > schema_dump.sql

backend:
	uvicorn app.main:app --reload

freeze:
	pip freeze > requirements.txt
