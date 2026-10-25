"""Tables + charts for the analysis questions. Usage: python analyze_news.py"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import config


def main():
    path = config.PROCESSED_DIR / "pakistani_news_cleaned.csv"
    if not path.exists():
        print("Run combine_datasets.py first.")
        return
    df = pd.read_csv(path, dtype={"published_date": str})
    out = config.REPORT_DIR
    out.mkdir(parents=True, exist_ok=True)
    df["date"] = pd.to_datetime(df["published_date"], errors="coerce")
    df["month"] = df["date"].dt.to_period("M").astype(str)
    dated = df.dropna(subset=["date"])

    # Q1 + Q2
    cat_by_source = pd.crosstab(df["source"], df["category"])
    cat_by_source.to_csv(out / "category_by_source.csv")
    dist = df["category"].value_counts()
    dist.to_csv(out / "category_distribution.csv")

    # Q3 + Q4
    ev = dated[dated["event_tag"] != "other"]
    ev.groupby(["month", "event_tag"]).size().unstack(fill_value=0).to_csv(out / "event_by_month.csv")
    pd.crosstab(df["source"], df["event_tag"]).to_csv(out / "event_by_source.csv")

    # Q5
    per_month = dated.groupby(["month", "source"]).size().unstack(fill_value=0)
    per_month.to_csv(out / "source_by_month.csv")

    # charts
    dist.plot(kind="bar", title="Articles per category")
    plt.tight_layout(); plt.savefig(out / "chart_category_distribution.png"); plt.close()

    cat_by_source.plot(kind="bar", stacked=True, figsize=(9, 5), title="Category by source")
    plt.tight_layout(); plt.savefig(out / "chart_category_by_source.png"); plt.close()

    if len(per_month):
        per_month.plot(figsize=(10, 5), title="Articles per month by source")
        plt.tight_layout(); plt.savefig(out / "chart_source_by_month.png"); plt.close()

    print("Rows analysed:", len(df))
    print("\nCategory distribution:\n", dist.to_string())
    print("\nCategory by source:\n", cat_by_source.to_string())
    print("\nSaved tables and charts in reports/")


if __name__ == "__main__":
    main()
