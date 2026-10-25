@echo off
call .venv\Scripts\activate
set /p M=Which member are you (1 or 2)? 
python scrape_news.py --member %M% --limit 20 --shuffle
echo.
echo Now open data\raw\member%M%_raw.csv and check headline, body, date and source look right.
pause
