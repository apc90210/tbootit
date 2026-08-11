#!/bin/bash
set -e

# Start Xvfb virtual framebuffer display :99
Xvfb :99 -screen 0 1280x1024x24 &
sleep 1

# Start x11vnc server pointing to :99 display on port 5900
x11vnc -display :99 -forever -shared -nopw -rfbport 5900 &
sleep 1

# Start noVNC websockify server mapping web port 6080 to VNC port 5900
/usr/share/novnc/utils/novnc_proxy --vnc localhost:5900 --listen 6080 &
sleep 1

echo "Browser VNC & noVNC runtime started successfully."

# Start FastAPI application
exec uvicorn app.main:app --host 0.0.0.0 --port 8020
