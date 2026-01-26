#!/bin/bash
set -e
echo "Reinitializing database..."

# Load environment variables from .env
export $(grep -v '^#' .env | xargs)

# Check the connection string
echo "Using database: $DATABASE_URL"

psql -q $DATABASE_URL -f prisma/seed_firms.sql

echo "Seeded database from prisma/seed_firms.sql"