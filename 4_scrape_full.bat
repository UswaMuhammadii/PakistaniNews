@echo off
call .venv\Scripts\activate
set /p M=Which member are you (1 or 2)? 
set /p L=Articles to save PER source (e.g. 15000)? 
python scrape_news.py --member %M% --limit %L% --shuffle
echo.
echo If it stopped, just run this file again. It continues where it left off.
pause
