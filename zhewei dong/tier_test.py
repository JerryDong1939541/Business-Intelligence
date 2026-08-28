"""Measure the achievable US sample size under different title definitions.

Runs each candidate title pattern through the same pipeline (state parsing +
deduplication) so the resulting counts are directly comparable.
"""
import pandas as pd

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
CODES = set(STATE_NAME_TO_CODE.values())


def state_of(loc):
    """Return the two-letter state code for a job_location, or None."""
    if not isinstance(loc, str):
        return None
    p = [x.strip() for x in loc.split(",")]
    if p[-1] in CODES:
        return p[-1]
    if p[-1].lower() in ("united states", "usa", "us") and len(p) >= 2:
        return STATE_NAME_TO_CODE.get(p[-2].lower())
    return None


a = pd.read_csv("analyst_raw.csv", dtype=str)
a["st"] = a.job_location.apply(state_of)


def pipeline(mask, label):
    sub = a[mask]
    us = sub[sub.st.notna()]
    ded = us.drop_duplicates(subset=["job_title", "company", "job_location"])
    covered = ded.st.nunique()
    small = (ded.st.value_counts() < 20).sum() + (51 - covered)
    print(f"{label:<36} {len(sub):>6,} {len(us):>6,} {len(ded):>6,}   {covered:>2}/51   {small:>2}")


t = a.job_title.str.lower()
print(f"{'Title definition':<36} {'World':>6} {'US':>6} {'Dedup':>6}  {'States':>6}  Low-n")
print("-" * 82)
pipeline(t.str.contains("business analyst", na=False),
         "business analyst (current)")
pipeline(t.str.contains(r"business (?:systems?|intelligence) analyst", regex=True, na=False),
         "  business systems/intel analyst")
pipeline(t.str.contains(r"business.*analyst", regex=True, na=False),
         "business ... analyst (any infix)")
pipeline(t.str.contains("data analyst", na=False),      "data analyst")
pipeline(t.str.contains("financial analyst", na=False), "financial analyst")
pipeline(t.str.contains("systems analyst", na=False),   "systems analyst")
pipeline(pd.Series(True, index=a.index),                "any title containing 'analyst' (ceiling)")
