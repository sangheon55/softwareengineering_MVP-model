@echo off
cd /d "%~dp0"
if not exist venv (
    echo [pick!ture] venv not found. Please follow the setup steps in README.md first.
    pause
    exit /b 1
)
call venv\Scripts\activate
echo [pick!ture] Starting server at http://localhost:8000 ...
uvicorn backend.main:app --host 127.0.0.1 --port 8000
