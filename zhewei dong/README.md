# State-Level Density of Business Analysis Skill Jobs

Individual analysis · Business Intelligence group assignment

Measures how many job postings requiring Business Analysis skills exist per
100,000 civilian labor force in each US state, using the group's shared cleaned
dataset as the numerator and US Census ACS data as the denominator. Output feeds
a state-level choropleth in Tableau.

## Research question

Once divided by labor force, does the geographic pattern differ from raw job counts?

**Yes.** Raw job count correlates with labor force at Pearson r = 0.942 (explaining
88.8% of variance) — a raw-count map is essentially a population map. Density
correlates at r = 0.008, carrying information independent of population size.

## Data sources

| Data | Source | Location |
|---|---|---|
| Job postings | Group cleaned dataset (KNIME) | `../shared_cleaned_data/BA_related_US_jobs_2024_cleaned.csv` |
| Labor force | US Census Bureau, ACS 1-Year 2024, Table B23025 | `ACSDT1Y2024.B23025-2026-08-21T171316.csv` (in this folder) |

The original Kaggle source ("1.3M LinkedIn Jobs & Skills 2024", 415 MB) is not in
this repository. It is only needed to re-run the legacy exploration scripts.

## Requirements

```
Python 3.13
pandas >= 2.0
```

```bash
pip install pandas
```

## How to reproduce

Copy `BA_related_US_jobs_2024_cleaned.csv` from `shared_cleaned_data/` into this
folder, then:

```bash
python3 clean_skill_density.py
```

| Output | Rows | Purpose |
|---|---|---|
| `ba_skill_state_density.csv` | 51 | **Tableau data source** |
| `ba_skill_us_clean.csv` | 5,228 | Posting-level detail (includes job_skills) |
| `ba_skill_excluded.csv` | 127 | Excluded records, for completeness reporting |

## Pipeline

```
5,466  source rows (job_skills contains "Business Analysis")
5,339  state resolved, 97.68%   <- 127 excluded (99 non-US or metro-area, 28 no state)
5,228  after deduplication, -111 <- final sample
```

### State resolution

Two rules, applied in order:

1. The trailing segment of `job_location` matches one of the 50 state codes or DC
2. The trailing segment is `United States` and the segment before it is a full state name

**`search_country` is deliberately not used to filter for US postings.** That field
records the country the crawler searched from, not where the job is located. Three
postings in Troy, Dearborn and Detroit, Michigan carry `search_country = Canada`
because the search city was Windsor, across the river. Filtering on it drops real US
jobs and admits foreign ones — 25 non-US postings (Vancouver, Tijuana, Istanbul and
others) remain in the shared dataset for this reason, and are removed here.

### Deduplication

Key: `(job_title, company, job_location)`. `job_link` is fully unique and therefore
useless as a dedup key.

Reposting the same role in the same city does not represent multiple openings, and
this behaviour clusters in specific companies — leaving duplicates in would
systematically inflate states hosting large consulting and outsourcing firms. The
result is a conservative estimate.

## Output fields

`ba_skill_state_density.csv`:

| Field | Description |
|---|---|
| `state_code` / `state_name` | 50 states plus DC |
| `skill_jobs` | Job count for the state |
| `labor_force` | ACS 2024 civilian labor force |
| `BA_skill_jobs_per_100k` | `skill_jobs / labor_force * 100000` |
| `rank_abs` / `rank_density` | Rank by raw count / by density |
| `rank_shift` | Positive means the state ranks higher per capita |
| `low_sample_flag` | Fewer than 20 jobs — density value is unreliable |

## What this metric means

**This measures the density of jobs requiring Business Analysis skills, not the
density of Business Analyst positions.**

Selection is based on the skills field rather than the job title. Title composition
of the sample:

| Function | Share |
|---|---|
| Business Analyst family | 32.5% |
| Manager / Director | 32.9% |
| Other Analyst roles | 13.3% |
| Engineer / Architect | 6.1% |
| Tax / Accounting | 2.6% |

## Known limitations

- **The observation window is only 5 days** (2024-01-12 to 2024-01-17). The metric
  counts postings that first appeared in that window — it is neither an annual total
  nor a stock of open positions. All states share the same window, so relative
  comparison between states remains valid.
- **13 states have fewer than 20 postings**, together only 2.28% of the sample. Their
  density values are highly sensitive to individual postings: one posting shifts
  Vermont (11 jobs) by ±9%, versus ±0.19% for California (520 jobs).
- **DC is an extreme outlier**, z-score 6.26 against 1.39 for second-place Virginia.
  A choropleth needs quantile binning or a log scale, otherwise the remaining 50
  states collapse into an indistinguishable colour band.
- **Numerator and denominator span different time scales**: a 5-day snapshot against
  a 2024 annual average.

## Other scripts in this folder

These belong to an earlier stage that used a strict title definition (`job_title`
contains "business analyst", final sample 3,329). Superseded by the skill-based
definition above; kept as a process record and for cross-definition comparison.

| Script | Purpose |
|---|---|
| `explore.py` | Profile field structure and missing rates on a sample |
| `scan_analyst.py` | Single streaming pass over the raw file, broad 'analyst' capture |
| `clean_ba.py` | Strict-title cleaning and state resolution |
| `merge_density.py` | Join ACS labor force, compute density |
| `tier_test.py` | Measure achievable sample size under different title definitions |

`ba_state_density.csv` holds the 51-state result under that definition, usable for
comparing the two.
