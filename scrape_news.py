"""
Polite, restartable, sitemap-based news scraper.

Examples:
  python scrape_news.py --member 1 --discover-only          # check sitemaps first
  python scrape_news.py --member 1 --limit 20               # tiny test batch per source
  python scrape_news.py --member 1 --limit 15000            # real run (can be stopped and resumed)
  python scrape_news.py --member 1 --source dawn --limit 15000
"""
import argparse
import csv
import gzip
import json
import logging
import random
import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import requests
import trafilatura

import config

log = logging.getLogger("scraper")
FIELDS = ["headline", "body_text", "source", "published_date",
          "word_count", "url", "section_hint"]


def setup_logging():
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(config.LOG_DIR / "scraping.log", encoding="utf-8"),
                  logging.StreamHandler()],
    )


def canonical_url(url):
    """Lower-case host, drop fragment/query and trailing slash."""
    p = urlparse(url.strip())
    path = p.path.rstrip("/") or "/"
    return urlunparse((p.scheme.lower(), p.netloc.lower(), path, "", "", ""))


# ---------------------------------------------------------------- robots.txt
def load_robots(session, base):
    rp = RobotFileParser()
    try:
        r = session.get(base + "/robots.txt", timeout=config.TIMEOUT)
    except requests.RequestException as e:
        log.error("Cannot read robots.txt for %s (%s). Not crawling.", base, e)
        rp.disallow_all = True
        rp.modified()
        return rp
    if r.status_code == 200:
        rp.parse(r.text.splitlines())
    elif r.status_code in (401, 403):
        rp.disallow_all = True
    else:  # 404 etc. = no rules
        rp.parse([])
    rp.modified()  # marks robots as "checked" so can_fetch works
    return rp


# ---------------------------------------------------------------- sitemaps
def parse_sitemap_bytes(content):
    """Return ('index', [(loc, lastmod)]) or ('urls', [(loc, lastmod)])."""
    if content[:2] == b"\x1f\x8b":
        content = gzip.decompress(content)
    root = ET.fromstring(content)

    def tag(e):
        return e.tag.split("}")[-1]

    items = []
    for child in root:
        loc = lastmod = None
        for sub in child:
            t = tag(sub)
            if t == "loc":
                loc = (sub.text or "").strip()
            elif t == "lastmod":
                lastmod = (sub.text or "").strip()
        if loc:
            items.append((loc, lastmod))
    return ("index" if tag(root) == "sitemapindex" else "urls"), items


def discover(session, key, cfg, rp, since, max_urls, rediscover):
    cache = config.INTERIM_DIR / f"{key}_urls.txt"
    if cache.exists() and not rediscover:
        urls = [l.strip() for l in cache.read_text(encoding="utf-8").splitlines() if l.strip()]
        log.info("[%s] loaded %d cached URLs (use --rediscover to refresh)", key, len(urls))
        return urls

    pattern = re.compile(cfg["article_regex"])
    queue = list(dict.fromkeys((rp.site_maps() or []) + cfg["sitemaps"]))
    seen, found = set(), {}
    while queue and len(found) < max_urls:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        if not rp.can_fetch(config.USER_AGENT, sm):
            log.warning("[%s] robots.txt disallows sitemap %s", key, sm)
            continue
        try:
            r = session.get(sm, timeout=config.TIMEOUT)
            if r.status_code != 200:
                log.warning("[%s] sitemap %s -> HTTP %s", key, sm, r.status_code)
                continue
            kind, items = parse_sitemap_bytes(r.content)
        except Exception as e:
            log.warning("[%s] sitemap failed %s: %s", key, sm, e)
            continue
        if kind == "index":
            queue.extend(loc for loc, _ in items)
        else:
            for loc, lastmod in items:
                if config.SOURCES[key]["host"] not in urlparse(loc).netloc:
                    continue
                if not pattern.search(loc):
                    continue
                if since and lastmod and lastmod[:4].isdigit() and int(lastmod[:4]) < since:
                    continue
                found[canonical_url(loc)] = lastmod
        log.info("[%s] sitemaps read: %d | article URLs found: %d", key, len(seen), len(found))
        time.sleep(1.0)

    urls = list(found)
    config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text("\n".join(urls), encoding="utf-8")
    return urls


# ---------------------------------------------------------------- extraction
def extract(html_bytes, url, source_name):
    out = trafilatura.extract(
        html_bytes, url=url, output_format="json", with_metadata=True,
        include_comments=False, include_tables=False, include_images=False,
        favor_precision=True)
    if not out:
        return None, "no_text"
    d = json.loads(out)
    headline = (d.get("title") or "").strip()
    body = (d.get("text") or "").strip()
    if not headline:
        return None, "no_headline"
    words = len(body.split())
    if words < config.MIN_WORDS:
        return None, f"short_body(<{config.MIN_WORDS})"
    hints = " ; ".join(x for x in [d.get("categories"), d.get("tags")] if x)
    return {
        "headline": headline, "body_text": body, "source": source_name,
        "published_date": d.get("date") or "", "word_count": words,
        "url": url, "section_hint": hints,
    }, "ok"


# ---------------------------------------------------------------- crawl
def load_attempted(path):
    done = set()
    if path.exists():
        with open(path, encoding="utf-8", newline="") as f:
            for row in csv.reader(f):
                if row:
                    done.add(row[0])
    return done


def crawl_source(session, key, args, raw_path):
    cfg = config.SOURCES[key]
    base = "https://" + urlparse(cfg["sitemaps"][0]).netloc
    rp = load_robots(session, base)
    if rp.disallow_all:
        log.error("[%s] robots.txt forbids crawling. Skipping this source.", key)
        return 0

    urls = discover(session, key, cfg, rp, args.since, args.max_discover, args.rediscover)
    log.info("[%s] total candidate URLs: %d", key, len(urls))
    if args.discover_only:
        for u in urls[:5]:
            log.info("[%s] sample URL: %s", key, u)
        return 0

    attempted_path = config.INTERIM_DIR / f"attempted_{key}.csv"
    attempted = load_attempted(attempted_path)
    todo = [u for u in urls if u not in attempted]
    if args.shuffle:
        random.Random(42).shuffle(todo)
    # how many successes do we already have for this source?
    already_ok = 0
    if raw_path.exists():
        with open(raw_path, encoding="utf-8", newline="") as f:
            already_ok = sum(1 for r in csv.DictReader(f) if r.get("source") == cfg["name"])
    need = max(0, args.limit - already_ok)
    log.info("[%s] already scraped: %d | still need: %d | untried URLs: %d",
             key, already_ok, need, len(todo))

    new_file = not raw_path.exists()
    ok = tried = blocked = net_err = 0
    with open(raw_path, "a", encoding="utf-8", newline="") as raw_f, \
         open(attempted_path, "a", encoding="utf-8", newline="") as att_f:
        raw_w = csv.DictWriter(raw_f, fieldnames=FIELDS)
        att_w = csv.writer(att_f)
        if new_file:
            raw_w.writeheader()
        try:
            for url in todo:
                if ok >= need:
                    break
                if not rp.can_fetch(config.USER_AGENT, url):
                    att_w.writerow([url, "robots_disallow"])
                    continue
                tried += 1
                try:
                    r = session.get(url, timeout=config.TIMEOUT)
                except requests.RequestException as e:
                    net_err += 1
                    att_w.writerow([url, f"net_error:{type(e).__name__}"])
                    att_f.flush()
                    if net_err >= config.MAX_NET_ERRORS:
                        log.error("[%s] too many network errors in a row. Stopping.", key)
                        break
                    time.sleep(5)
                    continue
                net_err = 0

                if r.status_code in (403, 429):
                    blocked += 1
                    att_w.writerow([url, f"http_{r.status_code}"])
                    att_f.flush()
                    log.warning("[%s] HTTP %s (%d in a row)", key, r.status_code, blocked)
                    if blocked >= config.MAX_BLOCKED:
                        log.error("[%s] site is refusing us. Stopping (as the brief requires).", key)
                        break
                    wait = r.headers.get("Retry-After", "60")
                    time.sleep(int(wait) if wait.isdigit() else 60)
                    continue
                blocked = 0

                if r.status_code != 200:
                    att_w.writerow([url, f"http_{r.status_code}"])
                elif "html" not in r.headers.get("Content-Type", "").lower():
                    att_w.writerow([url, "not_html"])
                else:
                    row, reason = extract(r.content, url, cfg["name"])
                    if row:
                        raw_w.writerow(row)
                        raw_f.flush()
                        ok += 1
                        att_w.writerow([url, "ok"])
                    else:
                        att_w.writerow([url, reason])
                att_f.flush()

                if tried % 50 == 0:
                    log.info("[%s] tried %d | saved %d | success rate %.0f%%",
                             key, tried, ok, 100 * ok / tried)
                time.sleep(args.delay)
        except KeyboardInterrupt:
            log.info("[%s] stopped by user. Progress is saved; run again to resume.", key)
            raise
    log.info("[%s] finished: tried %d, saved %d", key, tried, ok)
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--member", type=int, choices=[1, 2], required=True)
    ap.add_argument("--source", choices=list(config.SOURCES), help="only this source")
    ap.add_argument("--limit", type=int, default=15000, help="target saved articles PER source")
    ap.add_argument("--delay", type=float, default=config.DELAY)
    ap.add_argument("--since", type=int, default=None, help="only URLs whose sitemap year >= this")
    ap.add_argument("--max-discover", type=int, default=200000)
    ap.add_argument("--discover-only", action="store_true")
    ap.add_argument("--rediscover", action="store_true")
    ap.add_argument("--shuffle", action="store_true", help="random order (spreads dates out)")
    args = ap.parse_args()

    setup_logging()
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = config.RAW_DIR / f"member{args.member}_raw.csv"

    session = requests.Session()
    session.headers.update({"User-Agent": config.USER_AGENT, "Accept-Language": "en"})

    sources = [args.source] if args.source else config.MEMBERS[args.member]
    try:
        for key in sources:
            crawl_source(session, key, args, raw_path)
    except KeyboardInterrupt:
        pass
    log.info("Done. Raw file: %s", raw_path)


if __name__ == "__main__":
    main()
