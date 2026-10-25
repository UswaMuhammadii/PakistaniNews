"""
Baseline (weak) automatic labels: category + event_tag.
Usage: python label_news.py
These are heuristics. Validate them manually (see reports/label_validation.csv).
"""
import re
from pathlib import Path

import pandas as pd

import config

_cat_re = {c: [re.compile(r"\b" + re.escape(k) + r"\b") for k in kws]
           for c, kws in config.CATEGORY_TEXT_KEYWORDS.items()}
_evt_re = {e: [re.compile(r"\b" + re.escape(p) + r"\b") for p in ps]
           for e, ps in config.EVENT_PHRASES.items()}


def label_category(headline, body, url, section_hint):
    # 1) section/URL metadata first
    meta = (str(url).lower() + " " + str(section_hint).lower())
    for cat, kws in config.CATEGORY_SECTION_KEYWORDS.items():
        if any(re.search(r"(^|[/\-_ ;])" + re.escape(k), meta) for k in kws):
            return cat
    # 2) phrase scoring
    h, b = str(headline).lower(), str(body).lower()[:1000]
    best, best_score = "other", 0
    for cat, regs in _cat_re.items():
        score = sum(3 * len(r.findall(h)) + len(r.findall(b)) for r in regs)
        if score > best_score:
            best, best_score = cat, score
    return best if best_score >= config.CATEGORY_MIN_SCORE else "other"


def in_window(event, date):
    wins = config.EVENT_WINDOWS.get(event)
    if not wins:
        return True
    if not isinstance(date, str) or not date:
        return False
    return any(a <= date <= b for a, b in wins)


def label_event(headline, body, date):
    h, b = str(headline).lower(), str(body).lower()
    best, best_score = "other", 0
    for ev, regs in _evt_re.items():
        if not in_window(ev, date):
            continue
        in_head = sum(len(r.findall(h)) for r in regs)
        in_body = sum(len(r.findall(b)) for r in regs)
        # a casual single mention in the body is NOT enough
        if in_head > 0 or in_body >= 2:
            score = 5 * in_head + in_body
            if score > best_score:
                best, best_score = ev, score
    return best


def main():
    files = sorted(config.INTERIM_DIR.glob("*_clean.csv"))
    if not files:
        print("No cleaned files in data/interim/. Run clean_news.py first.")
        return
    for f in files:
        df = pd.read_csv(f, dtype=str, keep_default_na=False)
        df["category"] = [label_category(h, b, u, s) for h, b, u, s in
                          zip(df["headline"], df["body_text"], df["url"], df["section_hint"])]
        df["event_tag"] = [label_event(h, b, d) for h, b, d in
                           zip(df["headline"], df["body_text"], df["published_date"])]
        out = config.INTERIM_DIR / f.name.replace("_clean", "_labelled")
        df.to_csv(out, index=False, encoding="utf-8")
        print(f"{f.name}: labelled {len(df)} rows -> {out.name}")
        print(df["category"].value_counts().to_string(), "\n")


if __name__ == "__main__":
    main()
