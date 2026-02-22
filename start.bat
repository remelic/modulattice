@echo off
start /b cmd /k "python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 >nul
start "" "http://localhost:8000/"