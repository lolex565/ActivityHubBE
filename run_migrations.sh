#!/usr/bin/env bash
set -e

DB_CONTAINER="postgres"
DB_USER="activityhub"
DB_NAME="activityhub_db"

echo "Running migrations..."

for migration in migrations/*.sql; do
  echo "Applying $migration"
  docker compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "$migration"
done

echo "Migrations completed."