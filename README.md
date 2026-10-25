# Pakistani and International News Analysis (Data Mining Project)

Goal: collect unique articles from Pakistani publishers and international news
organizations using their published sitemaps and RSS feeds.

- Member 1: Dawn, The Express Tribune, ARY News, Daily Times, Pakistan Observer, ProPakistani, Associated Press of Pakistan, Daily Pakistan.
- Member 2: The News, Geo News, BBC News, DW News, The Guardian, France 24.
- NHK World is configured as an optional source, but its article pages timed out during the connection test.

## Steps (Windows) - double-click in order
1. `1_setup.bat` - installs everything. Then edit `config.py` and put your real email in USER_AGENT.
2. `2_check_sources.bat` - counts article URLs found in each site's sitemaps and RSS feeds.
3. `3_test_scrape.bat` - saves 20 articles per source. OPEN THE CSV and check it.
4. `4_scrape_full.bat` - the real run. Safe to stop (Ctrl+C) and run again.
5. `5_process.bat` - after both members' raw files are in `data/raw/`: clean, label, combine, analyze.

## Tips
- RSS usually provides only recent articles; its history varies by publisher. Use a publisher's sitemap when available for older articles.
- The default target is 15,000 saved articles per source, but a source may have fewer discoverable URLs.
- Speed is roughly 2-3 seconds per article. Run one source directly, for example `python scrape_news.py --member 2 --source bbc --limit 500`.
- The scraper obeys robots.txt, combines sitemap and official RSS article URLs, and deduplicates them.
- RSS is checked on every run, including when cached sitemap URLs are reused. Use `--rediscover` to refresh sitemaps too.
- The scraper stops a source if a site returns 403/429 five times.
- To check one publisher, run `python scrape_news.py --member 2 --source bbc --discover-only`.
- RSS feeds usually expose only recent articles; their available history varies by publisher.
- Final file: `data/processed/pakistani_news_cleaned.csv`.
- Reports: `reports/` (cleaning report, label validation sheet, tables, charts).
- Do not publish full article text. Respect each site's terms.
