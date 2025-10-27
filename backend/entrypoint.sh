#!/bin/sh

# Apply database migrations
echo "Applying database migrations..."
alembic upgrade head

# Start the FastAPI server
exec "$@"