"""Clean raw CSVs. Usage: python clean_news.py   (cleans every file in data/raw/)"""
import argparse
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pandas as pd

import config


def normalize_url(u):
    p = urlparse(str(u).strip())
    return urlunparse((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/") or "/", "", "", ""))


def norm_text(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", str(s).lower())).strip()


def canonical_source(s):
    return config.SOURCE_ALIASES.get(str(s).strip().lower(), str(s).strip())


def clean_file(src: Path, dst: Path, report: list):
    df = pd.read_csv(src, dtype=str, keep_default_na=False)
    report.append(f"== {src.name} ==")
    report.append(f"initial rows: {len(df)}")

    def drop(mask, reason):
        nonlocal df
        n = int(mask.sum())
        report.append(f"removed ({reason}): {n}")
        df = df[~mask].copy()

    df["url"] = df["url"].map(normalize_url)
    df["headline"] = df["headline"].str.replace(r"\s+", " ", regex=True).str.strip()
    df["body_text"] = df["body_text"].str.replace(r"[ \t]+", " ", regex=True) \
                                      .str.replace(r"\n{3,}", "\n\n", regex=True).str.strip()
    df["source"] = df["source"].map(canonical_source)

    drop(df["url"].duplicated(), "duplicate URL")
    drop(df["headline"] == "", "missing headline")
    df["word_count"] = df["body_text"].str.split().str.len()          # recalculated
    drop(df["word_count"] < config.MIN_WORDS, f"body shorter than {config.MIN_WORDS} words")

    d = pd.to_datetime(df["published_date"], errors="coerce", utc=True)
    df["published_date"] = d.dt.strftime("%Y-%m-%d")
    report.append(f"missing publication date (kept, excluded from time charts): {int(d.isna().sum())}")

    # flag near-duplicates (same normalised headline within this file)
    df["_h"] = df["headline"].map(norm_text)
    drop(df["_h"].duplicated(), "duplicate headline within file")
    df = df.drop(columns="_h")

    report.append(f"final rows: {len(df)}")
    for s, n in df["source"].value_counts().items():
        report.append(f"  per-source: {s}: {n}")
    report.append("")
    df.to_csv(dst, index=False, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", nargs="*", help="raw CSVs (default: data/raw/*.csv)")
    args = ap.parse_args()
    files = [Path(p) for p in args.input] if args.input else sorted(config.RAW_DIR.glob("*_raw.csv"))
    if not files:
        print("No raw files found in data/raw/. Run scrape_news.py first.")
        return
    config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    config.REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = []
    for f in files:
        clean_file(f, config.INTERIM_DIR / f.name.replace("_raw", "_clean"), report)
    (config.REPORT_DIR / "cleaning_report.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
