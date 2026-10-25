# Pakistani News Analysis (Data Mining Project)

Goal: 50,000+ unique articles from Dawn, The Express Tribune, The News, Geo News.
Member 1 = Dawn + Tribune. Member 2 = The News + Geo.

## Steps (Windows) - double-click in order
1. `1_setup.bat` - installs everything. Then edit `config.py` and put your real email in USER_AGENT.
2. `2_check_sources.bat` - counts article URLs found in each site's sitemap.
3. `3_test_scrape.bat` - saves 20 articles per source. OPEN THE CSV and check it.
4. `4_scrape_full.bat` - the real run. Safe to stop (Ctrl+C) and run again.
5. `5_process.bat` - after both members' raw files are in `data/raw/`: clean, label, combine, analyze.

## Tips
- Aim for about 15,000 per source (60,000 raw) so you still pass 50,000 after cleaning.
- Speed is roughly 2-3 seconds per article, so 15,000 takes ~10 hours per source.
  Open two terminals and run one source each (`--source dawn`, `--source tribune`).
- The scraper obeys robots.txt and stops if a site returns 403/429 five times.
- Final file: `data/processed/pakistani_news_cleaned.csv`.
- Reports: `reports/` (cleaning report, label validation sheet, tables, charts).
- Do not publish full article text. Respect each site's terms.
