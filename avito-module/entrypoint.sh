#!/bin/bash
set -e

echo "Starting Xvfb virtual framebuffer display :99..."
Xvfb :99 -screen 0 1280x1024x24 -ac &
sleep 2

echo "Starting x11vnc server on port 5900..."
x11vnc -display :99 -forever -shared -nopw -rfbport 5900 &
sleep 2

echo "Starting websockify / noVNC web server on 0.0.0.0:6080..."
websockify --web /usr/share/novnc 0.0.0.0:6080 localhost:5900 &
sleep 2

echo "Browser VNC & noVNC runtime processes initialized."

# Start FastAPI application
exec uvicorn app.main:app --host 0.0.0.0 --port 8020
