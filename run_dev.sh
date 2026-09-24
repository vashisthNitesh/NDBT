#!/bin/bash
# ==============================================================================
# NDBT Local Development Runner
# Starts both Django backend (port 8000) and Vue 3 frontend (port 5173)
# ==============================================================================

echo "🚀 Starting NDBT Transport Management System (Vue 3 + Django)..."

# Ensure frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
  echo "📦 Installing frontend dependencies..."
  cd frontend && npm install && cd ..
fi

# Build Vue frontend once for Django SPA serving
echo "🔨 Compiling Vue 3 static distribution..."
cd frontend && npm run build && cd ..

# Collect static files
.venv/bin/python manage.py collectstatic --noinput

echo "🌟 Starting Django Backend on http://127.0.0.1:8000 (Serving Vue 3 SPA + API + Admin)..."
.venv/bin/python manage.py runserver 127.0.0.1:8000 &
BACKEND_PID=$!

echo "⚡ Starting Vite Frontend Dev Server on http://localhost:5173 (with HMR)..."
cd frontend && npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

wait
