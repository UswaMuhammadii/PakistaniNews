"""
Combine both members' labelled files, deduplicate, check the target.
Usage: python combine_datasets.py --target 50000
"""
import argparse
import re

import pandas as pd

import config

COLUMNS = ["article_id", "headline", "body_text", "source", "published_date",
           "category", "event_tag", "word_count", "url"]


def norm_text(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", str(s).lower())).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=50000)
    ap.add_argument("--validation-sample", type=int, default=25, help="rows per source for manual review")
    args = ap.parse_args()

    files = sorted(config.INTERIM_DIR.glob("*_labelled.csv"))
    if not files:
        print("No labelled files. Run clean_news.py then label_news.py.")
        return
    df = pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False) for f in files], ignore_index=True)
    raw_total = len(df)

    df = df[~df["url"].duplicated()].copy()
    after_url = len(df)

    df["_h"] = df["headline"].map(norm_text)
    df["cross_source_dup"] = df["_h"].duplicated(keep=False)      # flagged: appears more than once
    df_all = df.copy()                                            # with flags, for auditing
    df = df[~df["_h"].duplicated()].copy()                        # keep first copy only
    df = df.drop(columns="_h")
    df["word_count"] = pd.to_numeric(df["word_count"], errors="coerce").astype("Int64")
    df.insert(0, "article_id", range(1, len(df) + 1))

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    config.REPORT_DIR.mkdir(parents=True, exist_ok=True)
    df[COLUMNS].to_csv(config.PROCESSED_DIR / "pakistani_news_cleaned.csv", index=False, encoding="utf-8")
    df_all.drop(columns="_h").to_csv(config.INTERIM_DIR / "all_with_duplicate_flags.csv",
                                     index=False, encoding="utf-8")

    # stratified sample for manual label validation
    parts = [g.sample(min(len(g), args.validation_sample), random_state=1)
             for _, g in df.groupby("source")]
    sample = pd.concat(parts)
    val = sample[["article_id", "source", "headline", "url", "category", "event_tag"]].copy()
    val["correct_category"] = ""
    val["correct_event_tag"] = ""
    val.to_csv(config.REPORT_DIR / "label_validation.csv", index=False, encoding="utf-8")

    lines = [
        f"rows before any combining dedupe : {raw_total}",
        f"after removing duplicate URLs     : {after_url}",
        f"after cross-source headline dedupe: {len(df)}   <- final unique records",
        f"target                            : {args.target}  ->  {'MET' if len(df) >= args.target else 'NOT MET'}",
        "", "per-source totals (final):", df["source"].value_counts().to_string(),
        "", "missing publication dates: " + str(int((df['published_date'] == '').sum()
                                                    + df['published_date'].isna().sum())),
    ]
    (config.REPORT_DIR / "combine_report.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
