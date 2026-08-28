"""Layer 2 (legacy, strict-title definition) - extract US Business Analyst jobs.

Rule: title contains 'business analyst' -> resolve state (two-letter code, or
state name followed by 'United States') -> deduplicate on
(job_title, company, job_location) -> write out.

Superseded by clean_skill_density.py, which uses the team's skill-based
definition. Kept as a process record and for cross-definition comparison.

Outputs: ba_us_clean.csv / ba_state_summary.csv / ba_excluded.csv
"""
import pandas as pd

STATE_NAME_TO_CODE = {
    "alabama":"AL","alaska":"AK","arizona":"AZ","arkansas":"AR","california":"CA",
    "colorado":"CO","connecticut":"CT","delaware":"DE","florida":"FL","georgia":"GA",
    "hawaii":"HI","idaho":"ID","illinois":"IL","indiana":"IN","iowa":"IA",
    "kansas":"KS","kentucky":"KY","louisiana":"LA","maine":"ME","maryland":"MD",
    "massachusetts":"MA","michigan":"MI","minnesota":"MN","mississippi":"MS",
    "missouri":"MO","montana":"MT","nebraska":"NE","nevada":"NV","new hampshire":"NH",
    "new jersey":"NJ","new mexico":"NM","new york":"NY","north carolina":"NC",
    "north dakota":"ND","ohio":"OH","oklahoma":"OK","oregon":"OR","pennsylvania":"PA",
    "rhode island":"RI","south carolina":"SC","south dakota":"SD","tennessee":"TN",
    "texas":"TX","utah":"UT","vermont":"VT","virginia":"VA","washington":"WA",
    "west virginia":"WV","wisconsin":"WI","wyoming":"WY",
    "district of columbia":"DC",
}
CODE_TO_NAME = {v: k.title() for k, v in STATE_NAME_TO_CODE.items()}
CODE_TO_NAME["DC"] = "District of Columbia"
STATE_CODES = set(STATE_NAME_TO_CODE.values())


def parse_state(loc):
    """Return (state_code, method); (None, reason) when unresolvable."""
    if not isinstance(loc, str) or not loc.strip():
        return None, "empty"
    parts = [p.strip() for p in loc.split(",")]
    tail = parts[-1]
    if tail in STATE_CODES:
        return tail, "state_code"
    if tail.lower() in ("united states", "usa", "us"):
        if len(parts) >= 2:
            code = STATE_NAME_TO_CODE.get(parts[-2].lower())
            if code:
                return code, "state_name"
        return None, "us_no_state"
    return None, "non_us_or_metro"


# ---------- 1. Load and filter to Business Analyst titles ----------
df = pd.read_csv("analyst_raw.csv", dtype=str)
ba = df[df["job_title"].str.contains("business analyst", case=False, na=False)].copy()
print(f"analyst_raw.csv                {len(df):>7,} rows")
print(f"  title has 'business analyst' {len(ba):>7,}")

# ---------- 2. Resolve state ----------
parsed = ba["job_location"].apply(parse_state)
ba["state_code"] = [p[0] for p in parsed]
ba["parse_method"] = [p[1] for p in parsed]

us = ba[ba["state_code"].notna()].copy()
excluded = ba[ba["state_code"].isna()].copy()
print(f"  resolved to a US state       {len(us):>7,}")
print(f"    - trailing state code      {(us.parse_method=='state_code').sum():>7,}")
print(f"    - recovered from full name {(us.parse_method=='state_name').sum():>7,}")
print(f"  excluded                     {len(excluded):>7,}")
print(excluded["parse_method"].value_counts().to_string())

# ---------- 3. Deduplicate ----------
DEDUP_KEY = ["job_title", "company", "job_location"]
n_before = len(us)
dups = us.duplicated(subset=DEDUP_KEY).sum()
us_dedup = us.drop_duplicates(subset=DEDUP_KEY, keep="first").copy()
print(f"\nDeduplicate on (job_title, company, job_location)")
print(f"  {n_before:,} -> {len(us_dedup):,}  (removed {dups:,}, {dups/n_before*100:.1f}%)")

us_dedup["state_name"] = us_dedup["state_code"].map(CODE_TO_NAME)

# ---------- 4. State summary (all 51 rows, zeros included) ----------
counts = us_dedup["state_code"].value_counts()
summary = pd.DataFrame({"state_code": sorted(STATE_CODES)})
summary["state_name"] = summary["state_code"].map(CODE_TO_NAME)
summary["ba_jobs"] = summary["state_code"].map(counts).fillna(0).astype(int)
summary["labor_force"] = pd.NA          # filled by merge_density.py
summary["BA_jobs_per_100k"] = pd.NA     # = ba_jobs / labor_force * 100000
summary["low_sample_flag"] = summary["ba_jobs"] < 20
summary = summary.sort_values("ba_jobs", ascending=False).reset_index(drop=True)

# ---------- 5. Write ----------
cols = ["job_link","job_title","company","job_location","state_code","state_name",
        "first_seen","job_level","job_type","search_city","search_country","parse_method"]
us_dedup[cols].to_csv("ba_us_clean.csv", index=False)
summary.to_csv("ba_state_summary.csv", index=False)
excluded[["job_link","job_title","company","job_location",
          "search_country","parse_method"]].to_csv("ba_excluded.csv", index=False)

print(f"\nOutputs:")
print(f"  ba_us_clean.csv       {len(us_dedup):>6,} rows  (detail)")
print(f"  ba_state_summary.csv  {len(summary):>6,} rows  (for Tableau)")
print(f"  ba_excluded.csv       {len(excluded):>6,} rows  (audit trail)")
print(f"\nAttrition: {len(excluded)/len(ba)*100:.2f}% non-US or no state"
      f" + {dups/n_before*100:.2f}% duplicates")
