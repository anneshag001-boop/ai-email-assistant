@echo off
cd /d D:\ai-email-assistant
start /B /MIN "" "D:\ai-email-assistant\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
echo Server started on port 8000
