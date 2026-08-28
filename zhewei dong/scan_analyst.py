"""Layer 1 - Single streaming pass over the full 415 MB source file.

Captures every posting whose title contains 'analyst' (deliberately broader
than the target definition) and writes them out unchanged. Run once: all
later filtering iterates on the small extract instead of the raw file.

Output: analyst_raw.csv
"""
import pandas as pd
import time

SRC = "linkedin_job_postings.csv"
OUT = "analyst_raw.csv"
CHUNK = 200_000

t0 = time.time()
total_rows = 0
total_hits = 0
first_write = True
country_counts = pd.Series(dtype="int64")

reader = pd.read_csv(SRC, chunksize=CHUNK, dtype=str)

for i, chunk in enumerate(reader, 1):
    total_rows += len(chunk)
    country_counts = country_counts.add(
        chunk["search_country"].value_counts(), fill_value=0
    )

    hits = chunk[chunk["job_title"].str.contains("analyst", case=False, na=False)]
    total_hits += len(hits)

    if len(hits):
        hits.to_csv(OUT, mode="w" if first_write else "a",
                    header=first_write, index=False)
        first_write = False

    print(f"  chunk {i:>2}  read {total_rows:>9,}  matched {total_hits:>7,}"
          f"  ({time.time()-t0:>5.1f}s)", flush=True)

print("\n" + "=" * 60)
print(f"Total rows:      {total_rows:,}")
print(f"'analyst' match: {total_hits:,}  ({total_hits/total_rows*100:.4f}%)")
print(f"Elapsed:         {time.time()-t0:.1f}s")
print("\nsearch_country distribution (full file):")
print(country_counts.astype(int).sort_values(ascending=False).to_string())
