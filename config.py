"""Shared settings. Edit this file, not the scripts."""
from pathlib import Path

ROOT = Path(__file__).parent
RAW_DIR = ROOT / "data" / "raw"
INTERIM_DIR = ROOT / "data" / "interim"
PROCESSED_DIR = ROOT / "data" / "processed"
LOG_DIR = ROOT / "logs"
REPORT_DIR = ROOT / "reports"

# >>> PUT YOUR REAL EMAIL HERE (a truthful User-Agent is required by the brief) <<<
USER_AGENT = "PakistaniNewsResearchBot/1.0 (university data-mining project; contact: uswamuhammadi@gmail.com)"

TIMEOUT = 60            # seconds per request; the live news sitemaps are slower and sometimes time out.
DELAY = 1.5             # seconds between article requests (be polite)
MIN_WORDS = 50          # minimum body words. Document your final choice in the report.
MAX_BLOCKED = 5         # stop a source after this many 403/429 in a row
MAX_NET_ERRORS = 25     # stop a source after this many network errors in a row

# Who scrapes what (from the brief)
MEMBERS = {1: ["dawn", "tribune"], 2: ["thenews", "geo"]}

# article_regex = pattern an article URL must match. VERIFY these with:
#   python scrape_news.py --member 1 --discover-only
SOURCES = {
    "dawn": {
        "name": "Dawn",
        "host": "dawn.com",
        "sitemaps": ["https://www.dawn.com/feeds/sitemap"],
        "article_regex": r"/(news|latest-news|latest|archive)/\d+|/news/\d+",
    },
    "tribune": {
        "name": "The Express Tribune",
        "host": "tribune.com.pk",
        "sitemaps": ["https://tribune.com.pk/sitemap.xml", "https://tribune.com.pk/sitemap/latest-1.xml"],
        "article_regex": r"/(story|blogs|videos)/\d+|/story/\d+",
    },
    "thenews": {
        "name": "The News International",
        "host": "thenews.com.pk",
        "sitemaps": ["https://www.thenews.com.pk/sitemap.xml"],
        "article_regex": r"/(latest|print|latest-stories)/\d+|/latest/\d+|/latest/[^/]+/\d+",
    },
    "geo": {
        "name": "Geo News",
        "host": "geo.tv",
        "sitemaps": ["https://www.geo.tv/assets/uploads/google_news_latest.xml"],
        "article_regex": r"/latest/\d+",
    },
}

# Map spelling variants to one canonical source name
SOURCE_ALIASES = {
    "dawn": "Dawn", "dawn.com": "Dawn", "dawn news": "Dawn",
    "the express tribune": "The Express Tribune", "express tribune": "The Express Tribune",
    "tribune": "The Express Tribune", "tribune.com.pk": "The Express Tribune",
    "the news international": "The News International", "the news": "The News International",
    "thenews.com.pk": "The News International",
    "geo news": "Geo News", "geo.tv": "Geo News", "geo": "Geo News",
}

# ---------------- Labelling rules (baseline / weak labels) ----------------
CATEGORIES = ["politics", "business", "sports", "world", "technology",
              "entertainment", "health", "other"]

# 1) section / URL keywords (checked first)
CATEGORY_SECTION_KEYWORDS = {
    "politics": ["politics", "parliament", "election"],
    "business": ["business", "economy", "finance", "markets"],
    "sports": ["sport", "cricket", "football", "hockey"],
    "world": ["world", "international"],
    "technology": ["tech", "science", "sci-tech"],
    "entertainment": ["entertainment", "showbiz", "culture"],
    "health": ["health"],
}

# 2) phrase scoring in headline (x3) and start of body (x1)
CATEGORY_TEXT_KEYWORDS = {
    "politics": ["national assembly", "senate", "prime minister", "pti", "pml-n", "ppp",
                 "parliament", "opposition", "chief minister", "political", "coalition", "cabinet"],
    "business": ["stock exchange", "psx", "kse-100", "rupee", "inflation", "state bank",
                 "sbp", "gdp", "exports", "imports", "tax", "fbr", "revenue", "trade deficit",
                 "budget", "imf", "petrol price", "diesel price", "fuel price", "bailout"],
    "sports": ["cricket", "match", "tournament", "pcb", "football", "olympic", "t20",
               "psl", "batsman", "wicket", "hockey", "squash", "world cup"],
    "world": ["united nations", "us president", "white house", "gaza", "israel", "china",
              "india", "afghanistan", "russia", "ukraine", "europe", "washington", "beijing"],
    "technology": ["artificial intelligence", "software", "smartphone", "internet", "pta",
                   "cyber", "startup", "app", "5g", "telecom", "google", "microsoft"],
    "entertainment": ["film", "drama", "actor", "actress", "singer", "showbiz", "celebrity",
                      "movie", "album", "bollywood", "lollywood"],
    "health": ["hospital", "doctor", "patients", "dengue", "polio", "vaccine", "disease",
               "health ministry", "medical", "virus", "cancer"],
}
CATEGORY_MIN_SCORE = 3

# Event rules: phrase list. Tag if a phrase is in the headline OR appears >= 2 times in body.
EVENT_PHRASES = {
    "budget": ["federal budget", "budget speech", "fiscal budget", "budget 20"],
    "elections": ["general election", "general elections", "polling station", "election results",
                  "election commission", "ecp", "polling day"],
    "floods": ["flood", "floods", "flooding", "flash flood", "flood relief", "flood-affected"],
    "imf": ["imf loan", "imf programme", "imf program", "bailout", "international monetary fund", "imf"],
    "fuel_prices": ["petrol price", "diesel price", "fuel price", "petroleum price",
                    "petroleum prices", "price of petrol"],
}
# Optional date windows per event, e.g. {"floods": [("2022-06-15", "2022-10-31")]}.
# Leave empty to use phrase rules only. If you fill one in, document the timeline in your report.
EVENT_WINDOWS = {}
