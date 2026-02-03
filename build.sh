#!/usr/bin/env bash
# exit on error
set -o errexit

# Install python dependencies
pip install -r requirements.txt

# Build the frontend
echo "Node version: $(node -v)"
echo "NPM version: $(npm -v)"
cd frontend
npm install
npm run build
cd ..

echo "Build complete!"
