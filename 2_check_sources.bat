@echo off
call .venv\Scripts\activate
set /p M=Which member are you (1 or 2)? 
python scrape_news.py --member %M% --discover-only
echo.
echo Look at the numbers above. 0 URLs may mean its sitemap, RSS feed, or URL pattern needs checking.
pause
