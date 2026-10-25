@echo off
call .venv\Scripts\activate
python clean_news.py
python label_news.py
python combine_datasets.py --target 50000
python analyze_news.py
pause
