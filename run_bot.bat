@echo off
if not exist .venv (
    echo Virtual environment not found. Creating...
    python -m venv .venv
    echo Installing dependencies...
    .venv\Scripts\pip install -r requirements.txt
)

echo Starting Discord Bot...
.venv\Scripts\python -m src.main
pause
