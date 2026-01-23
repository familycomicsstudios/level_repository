#!/bin/bash

# Build script for Vercel deployment
echo "Installing dependencies..."
pip install --break-system-packages -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Build complete!"
