"""Step 1 - Exploratory profiling of the raw LinkedIn dataset.

Read-only: inspects column names, missing rates, location formats and title
hit rates on a sample. Writes nothing to disk.
"""
import pandas as pd

N = 80_000
df = pd.read_csv("linkedin_job_postings.csv", nrows=N)

print("=" * 70)
print("1. Basic structure")
print("=" * 70)
print("Columns:", list(df.columns))
print("Shape:  ", df.shape)
print("\nMissing rate per column:")
print((df.isna().mean() * 100).round(2).astype(str) + " %")

print("\n" + "=" * 70)
print("2. job_location field")
print("=" * 70)
loc = df["job_location"]
print(f"Missing: {loc.isna().sum()}  ({loc.isna().mean()*100:.3f}%)")
print(f"Blank strings: {(loc.fillna('').str.strip() == '').sum()}")
print(f"Distinct formats: {loc.nunique()}")
print("\nTop 30 most common values:")
print(loc.value_counts().head(30).to_string())

print("\n--- Structure: number of comma-separated segments ---")
seg = loc.dropna().str.count(",") + 1
print(seg.value_counts().sort_index().to_string())

print("\n--- Top 30 trailing segments (text after the last comma) ---")
tail = loc.dropna().str.rsplit(",", n=1).str[-1].str.strip()
print(tail.value_counts().head(30).to_string())

print("\n" + "=" * 70)
print("3. search_country distribution (candidate US filter)")
print("=" * 70)
print(df["search_country"].value_counts(dropna=False).head(15).to_string())

print("\n" + "=" * 70)
print("4. Share of titles containing 'business analyst'")
print("=" * 70)
title = df["job_title"].fillna("")
ba = title.str.contains("business analyst", case=False, na=False)
print(f"Matched: {ba.sum()} / {len(df)}  ({ba.mean()*100:.4f}%)")

print("\nTop 30 matched titles:")
print(df.loc[ba, "job_title"].value_counts().head(30).to_string())

print("\nTop 20 locations among matched postings:")
print(df.loc[ba, "job_location"].value_counts().head(20).to_string())

print("\n--- Reference: share of the broader 'analyst' pattern ---")
print(f"{title.str.contains('analyst', case=False, na=False).mean()*100:.4f}%")
