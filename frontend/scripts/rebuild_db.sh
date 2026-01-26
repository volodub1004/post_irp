#!/bin/bash
set -e  # Exit immediately if a command fails

echo " Rebuilding and seeding Postgres database (irpdb)"

# Load environment variables from .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo "No .env file found in current directory."
  exit 1
fi

# Extract parts from DATABASE_URL (for psql commands)
PG_USER=$(echo "$DATABASE_URL" | sed -E 's|postgresql://([^:]+):.*|\1|')
PG_PASS=$(echo "$DATABASE_URL" | sed -E 's|postgresql://[^:]+:([^@]+)@.*|\1|')
PG_HOST=$(echo "$DATABASE_URL" | sed -E 's|postgresql://[^@]+@([^:/]+):.*|\1|')
PG_PORT=$(echo "$DATABASE_URL" | sed -E 's|.*:([0-9]+)/.*|\1|')
PG_DB=$(echo "$DATABASE_URL"   | sed -E 's|.*/([^/?]+).*|\1|')

export PGPASSWORD=$PG_PASS

echo "Using database: $PG_DB on host $PG_HOST:$PG_PORT"

# Terminate active connections to irpdb
echo "Terminating active sessions..."
sudo -u postgres psql -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${PG_DB}' AND pid <> pg_backend_pid();" >/dev/null || true

# Drop and recreate database
echo "Dropping existing database (if exists)..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${PG_DB};"
echo "Creating new database..."
sudo -u postgres psql -c "CREATE DATABASE ${PG_DB};"

# Clean migrations and generated client
echo "Cleaning old Prisma artifacts..."
rm -rf prisma/migrations
rm -rf src/generated/prisma

# Run Prisma migration and codegen
echo "Running Prisma migration + generate..."
npx prisma migrate dev --name init --skip-generate
npx prisma generate

# Seed the database
if [ -f "prisma/seed_firms.sql" ]; then
  echo "Seeding database from prisma/seed_firms.sql..."
  psql -q $DATABASE_URL -f prisma/seed_firms.sql
else
  echo "Warning: seed_firms.sql not found, skipping seeding."
fi

echo "Database rebuild complete."
