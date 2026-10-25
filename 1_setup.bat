@echo off
echo Creating virtual environment and installing libraries...
python -m venv .venv
call .venv\Scripts\activate
python -m pip install -r requirements.txt
python -c "import requests, bs4, pandas, trafilatura; print('Setup successful')"
echo.
echo NEXT: open config.py and put your real email in USER_AGENT.
pause
