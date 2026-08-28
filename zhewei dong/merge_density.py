"""Layer 3 (legacy) - join ACS state labor force and compute BA_jobs_per_100k.

Inputs:  ba_state_summary.csv + ACS B23025 wide table
Output:  ba_state_density.csv

Superseded by clean_skill_density.py. Kept for cross-definition comparison.
"""
import pandas as pd

ACS = "ACSDT1Y2024.B23025-2026-08-21T171316.csv"
DROP_GEO = {"United States", "Puerto Rico"}

# ---------- 1. Pull the Civilian labor force row out of the ACS wide table ----------
raw = pd.read_csv(ACS, dtype=str)
row = raw[raw["Label (Grouping)"].str.strip() == "Civilian labor force:"].iloc[0]

lf = {}
for col, val in row.items():
    if "!!" not in col:
        continue
    geo, kind = col.split("!!")[0], col.split("!!")[-1]
    if kind != "Estimate" or geo in DROP_GEO:
        continue
    lf[geo] = int(str(val).replace(",", ""))

acs = pd.DataFrame({"state_name": list(lf), "labor_force": list(lf.values())})
print(f"ACS: {len(acs)} states, total civilian labor force {acs.labor_force.sum():,}")

# ---------- 2. Merge ----------
s = pd.read_csv("ba_state_summary.csv").drop(columns=["labor_force", "BA_jobs_per_100k"])
m = s.merge(acs, on="state_name", how="outer", indicator=True)

bad = m[m["_merge"] != "both"]
if len(bad):
    print("!! Unmatched rows:")
    print(bad[["state_code", "state_name", "_merge"]].to_string(index=False))
else:
    print(f"Merged {len(m)}/51 states, no unmatched rows")
m = m.drop(columns=["_merge"])

# ---------- 3. Compute ----------
m["BA_jobs_per_100k"] = (m["ba_jobs"] / m["labor_force"] * 100_000).round(3)
m["rank_abs"] = m["ba_jobs"].rank(ascending=False, method="min").astype(int)
m["rank_density"] = m["BA_jobs_per_100k"].rank(ascending=False, method="min").astype(int)
m["rank_shift"] = m["rank_abs"] - m["rank_density"]   # positive = rises on a per-capita basis

m = m.sort_values("BA_jobs_per_100k", ascending=False).reset_index(drop=True)
m = m[["state_code","state_name","ba_jobs","labor_force","BA_jobs_per_100k",
       "rank_abs","rank_density","rank_shift","low_sample_flag"]]
m.to_csv("ba_state_density.csv", index=False)

print(f"\nNational weighted average: {m.ba_jobs.sum()/m.labor_force.sum()*100000:.3f} per 100k")
print("\n" + "=" * 88)
print(m.to_string(index=False))
