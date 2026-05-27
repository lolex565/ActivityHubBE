#!/usr/bin/env bash
set -e

DB_CONTAINER="activityhub-db"
DB_USER="postgres"
DB_NAME="activityhub"

echo "Running migrations..."

for migration in migrations/*.sql; do
  echo "Applying $migration"
  docker compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "$migration"
done

echo "Migrations completed."