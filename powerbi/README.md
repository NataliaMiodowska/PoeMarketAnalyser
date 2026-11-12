# Power BI dashboard

Power BI Desktop version: 2.149.1429.0 64-bit (November 2025)

**Status: in progress.** Data model and DAX measures are done and validated; report pages are built and being finalised (texts, screenshots).

## Data

The report loads the aggregated CSV files from `powerbi/data/`, prepared by `export_for_powerbi.py`
(written by Claude Code) from the processed project data.

| Table | Rows | Grain |
|---|---|---|
| `fact_daily_league` | 916 | league × day: currency index, daily index change, players, market value |
| `fact_item_weekly` | 575,241 | league × week × item: median price |
| `fact_item_daily_top` | 254,936 | league × day × item, top items only: daily price |
| `dim_item` | 8,803 | item, 37 categories |
| `dim_league` | 6 | league dates and cluster |
| `dim_date` | 928 | calendar table (DAX `CALENDAR`), 2023-08-18 to 2026-03-02, marked as date table; calculated columns `phase` and `league_day` taken from `fact_daily_league` |

Star schema: facts are related to the dimensions many-to-one with single-direction filtering.
Leagues do not overlap in time, so each date belongs to one league at most. This is why the league phase is stored in `dim_date`: a phase slicer then filters all fact tables, and every phase exists in every league.

## DAX measures

| Folder | Measures |
|---|---|
| Prices | Median Price, DoD % Change, Price Change Rank, Item Price Variability |
| Market | Currency Index, Price Volatility, Avg Daily Index Change, League Cluster, Top 1% Share |
| Players | Avg Players, Market Value per Player |

## Validation

DAX results were exported from Power BI (*Export data*) to `powerbi/validation/` and compared with the same
measures computed in pandas from `powerbi/data/` by [`validation/validation.py`](validation/validation.py)
(written by Claude Code). Run it from the repository folder:

```bash
python powerbi/validation/validation.py
```

**Measures vs pandas** (tolerance: relative difference below 0.1 %; Power BI exports rounded values):

| League | Measure | Power BI | pandas | Difference |
|---|---|---|---|---|
| Keepers | Median Price | 3.80 | 3.80 | 0.000 % |
| Keepers | Currency Index | 1.505 | 1.5055 | 0.031 % |
| Keepers | Avg Players | 33,187 | 33,186.6 | 0.001 % |
| Keepers | Top 1% Share | 77.28 % | 77.28 % | 0.001 % |
| Necropolis | Median Price | 5.00 | 5.00 | 0.000 % |
| Necropolis | Currency Index | 1.772 | 1.7724 | 0.025 % |
| Necropolis | Avg Players | 32,586 | 32,586.0 | 0.000 % |
| Necropolis | Top 1% Share | 84.91 % | 84.91 % | 0.004 % |

**Price Volatility** (standard deviation of the daily currency index change, `STDEV.S`) matches
`league_phase_summary.csv` from notebook 06 for all 24 league × phase combinations (absolute difference below 1e-6).

**Expected differences** (not errors, described here instead of being corrected):
- Player counts are joined to the daily data by date, while notebook 06 joins them by league day,
  so average player numbers can differ slightly from `population_economy.csv`.
- Duplicate item prices were collapsed with the median during the export, so median price,
  top 1% share and market value can differ slightly from notebook 07.
- Weekly prices are assigned to a phase by the week's start date, so phase boundaries for Median Price
  and Top 1% Share can be shifted by a few days.
