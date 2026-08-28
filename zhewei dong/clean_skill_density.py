"""State-level density of jobs requiring Business Analysis skills.

Input is the team's shared cleaned dataset (selected by the job_skills field
containing "Business Analysis"). This script resolves each posting to a US
state, deduplicates, joins ACS 2024 civilian labor force, and computes the
per-capita density used for the Tableau choropleth.

Metric: BA_skill_jobs_per_100k
        = jobs requiring Business Analysis skills / civilian labor force x 100,000

Outputs: ba_skill_us_clean.csv / ba_skill_state_density.csv / ba_skill_excluded.csv
"""
import pandas as pd

SRC = "BA_related_US_jobs_2024_cleaned.csv"
ACS = "ACSDT1Y2024.B23025-2026-08-21T171316.csv"

STATE_NAME_TO_CODE = {
 "alabama":"AL","alaska":"AK","arizona":"AZ","arkansas":"AR","california":"CA","colorado":"CO",
 "connecticut":"CT","delaware":"DE","florida":"FL","georgia":"GA","hawaii":"HI","idaho":"ID",
 "illinois":"IL","indiana":"IN","iowa":"IA","kansas":"KS","kentucky":"KY","louisiana":"LA",
 "maine":"ME","maryland":"MD","massachusetts":"MA","michigan":"MI","minnesota":"MN",
 "mississippi":"MS","missouri":"MO","montana":"MT","nebraska":"NE","nevada":"NV",
 "new hampshire":"NH","new jersey":"NJ","new mexico":"NM","new york":"NY","north carolina":"NC",
 "north dakota":"ND","ohio":"OH","oklahoma":"OK","oregon":"OR","pennsylvania":"PA",
 "rhode island":"RI","south carolina":"SC","south dakota":"SD","tennessee":"TN","texas":"TX",
 "utah":"UT","vermont":"VT","virginia":"VA","washington":"WA","west virginia":"WV",
 "wisconsin":"WI","wyoming":"WY","district of columbia":"DC"}
CODE_TO_NAME = {v: k.title() for k, v in STATE_NAME_TO_CODE.items()}
CODE_TO_NAME["DC"] = "District of Columbia"
CODES = set(STATE_NAME_TO_CODE.values())


def parse_state(loc):
    """Resolve a job_location string to a US state code.

    Two rules, in order:
      1. trailing segment is one of the 50 state codes or DC   -> use it
      2. trailing segment is "United States" and the segment
         before it is a full state name                        -> map it

    search_country is deliberately NOT used: it records the country the
    crawler searched from, not where the job is. Three postings in Troy,
    Dearborn and Detroit MI carry search_country=Canada because the search
    city was Windsor, across the river.

    Returns (state_code, method) or (None, reason).
    """
    if not isinstance(loc, str) or not loc.strip():
        return None, "empty"
    p = [x.strip() for x in loc.split(",")]
    if p[-1] in CODES:
        return p[-1], "state_code"
    if p[-1].lower() in ("united states", "usa", "us"):
        if len(p) >= 2 and p[-2].lower() in STATE_NAME_TO_CODE:
            return STATE_NAME_TO_CODE[p[-2].lower()], "state_name"
        return None, "us_no_state"
    return None, "non_us_or_metro"


# ---------- 1. Load ----------
d = pd.read_csv(SRC, dtype=str)
print(f"Source: {SRC}")
print(f"  {len(d):,} rows x {d.shape[1]} columns")

# Drop the redundant join artifact if present
if "job_link (Right)" in d.columns:
    assert (d["job_link"] == d["job_link (Right)"]).all(), \
        "job_link (Right) does not match job_link"
    d = d.drop(columns=["job_link (Right)"])
    print("  dropped redundant column: job_link (Right)")

# ---------- 2. Resolve state ----------
parsed = d["job_location"].apply(parse_state)
d["state_code"] = [p[0] for p in parsed]
d["parse_method"] = [p[1] for p in parsed]

us = d[d.state_code.notna()].copy()
exc = d[d.state_code.isna()].copy()
print(f"\nState resolution:")
print(f"  resolved                   {len(us):>6,}  ({len(us)/len(d)*100:.2f}%)")
print(f"    - trailing state code    {(us.parse_method=='state_code').sum():>6,}")
print(f"    - recovered from name    {(us.parse_method=='state_name').sum():>6,}")
print(f"  excluded                   {len(exc):>6,}")
print(exc.parse_method.value_counts().to_string())

# ---------- 3. Deduplicate ----------
# job_link is fully unique, so it cannot serve as a dedup key. Reposting the
# same role in the same city is not the same as multiple openings, and such
# reposting clusters in specific companies, which would inflate those states.
KEY = ["job_title", "company", "job_location"]
n0 = len(us)
dups = us.duplicated(subset=KEY).sum()
us = us.drop_duplicates(subset=KEY, keep="first").copy()
print(f"\nDeduplicate on (job_title, company, job_location):")
print(f"  {n0:,} -> {len(us):,}  (removed {dups:,}, {dups/n0*100:.2f}%)")

us["state_name"] = us.state_code.map(CODE_TO_NAME)

# ---------- 4. ACS civilian labor force ----------
raw = pd.read_csv(ACS, dtype=str)
row = raw[raw["Label (Grouping)"].str.strip() == "Civilian labor force:"].iloc[0]
lf = {c.split("!!")[0]: int(str(v).replace(",", ""))
      for c, v in row.items()
      if "!!" in c and c.endswith("Estimate")
      and c.split("!!")[0] not in {"United States", "Puerto Rico"}}
acs = pd.DataFrame({"state_name": list(lf), "labor_force": list(lf.values())})

# ---------- 5. State summary ----------
counts = us.state_code.value_counts()
s = pd.DataFrame({"state_code": sorted(CODES)})
s["state_name"] = s.state_code.map(CODE_TO_NAME)
s["skill_jobs"] = s.state_code.map(counts).fillna(0).astype(int)
s = s.merge(acs, on="state_name", how="left", indicator=True)
assert (s._merge == "both").all(), "some states did not match ACS"
s = s.drop(columns=["_merge"])
print(f"\nACS merge: {len(s)}/51 states matched")

s["BA_skill_jobs_per_100k"] = (s.skill_jobs / s.labor_force * 100_000).round(3)
s["rank_abs"] = s.skill_jobs.rank(ascending=False, method="min").astype(int)
s["rank_density"] = s.BA_skill_jobs_per_100k.rank(ascending=False, method="min").astype(int)
s["rank_shift"] = s.rank_abs - s.rank_density
s["low_sample_flag"] = s.skill_jobs < 20
s = s.sort_values("BA_skill_jobs_per_100k", ascending=False).reset_index(drop=True)

# ---------- 6. Write ----------
detail_cols = ["job_link","job_title","company","job_location","state_code","state_name",
               "job_skills","first_seen","job_level","job_type","search_city","parse_method"]
us[detail_cols].to_csv("ba_skill_us_clean.csv", index=False)
s.to_csv("ba_skill_state_density.csv", index=False)
exc[["job_link","job_title","company","job_location","parse_method"]].to_csv(
    "ba_skill_excluded.csv", index=False)

print(f"\nOutputs:")
print(f"  ba_skill_us_clean.csv       {len(us):>6,} rows")
print(f"  ba_skill_state_density.csv  {len(s):>6,} rows  (for Tableau)")
print(f"  ba_skill_excluded.csv       {len(exc):>6,} rows")
print(f"\nNational weighted average "
      f"{s.skill_jobs.sum()/s.labor_force.sum()*100000:.3f} per 100k labor force")
print(f"Low-sample states (n<20): {s.low_sample_flag.sum()}")
print(f"States with zero jobs: {s[s.skill_jobs==0].state_code.tolist() or 'none'}")
print("\n" + "=" * 92)
print(s.to_string(index=False))
