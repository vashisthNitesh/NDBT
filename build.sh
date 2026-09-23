#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Collect static files for WhiteNoise
python3 manage.py collectstatic --no-input

# Run database migrations
python3 manage.py migrate

# Seed permission groups (Admin, Accounts, Data Entry, Viewer)
python3 manage.py seed_groups
