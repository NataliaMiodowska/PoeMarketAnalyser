"""Check Power BI measures against pandas. Written by Claude Code (AI assistant).

Run from the repo folder:
    python powerbi/validation/validation.py

Inputs (exported from Power BI with "Export data", saved in powerbi/validation/):
    pbi_measures.csv    - table: league, Median Price, Currency Index, Avg Players, Top 1% Share
    pbi_volatility.csv  - table: league, phase, Price Volatility   (optional, checked if present)

The script recomputes the same numbers in pandas from powerbi/data/
and prints OK / CHECK for every league and measure.
"""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent.parent             # ...\powerbi
DATA = HERE / "data"                                # CSV files loaded into Power BI
VALIDATION = HERE / "validation"                    # exports from Power BI
PHASE_SUMMARY = HERE.parent / "data" / "players_data_processed" / "league_phase_summary.csv"

TOLERANCE = 0.001        # measures: relative difference below 0.1 %
                         # (Power BI exports rounded values, e.g. 3,80 or 77,28 %)
VOL_TOLERANCE = 1e-6     # Price Volatility: absolute difference


def to_number(column):
    """Turn Power BI text like '1,505', '77,28%' or '33 187' into floats."""
    text = column.astype(str).str.strip()
    is_percent = text.str.endswith("%")
    text = (text.str.replace("%", "", regex=False)
                .str.replace(" ", "", regex=False)   # non-breaking space (thousands)
                .str.replace(" ", "", regex=False)
                .str.replace(",", ".", regex=False))      # decimal comma -> dot
    numbers = pd.to_numeric(text)
    return numbers.where(~is_percent, numbers / 100)


def read_pbi(path):
    """Read a Power BI export; all columns except text keys become numbers."""
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")   
    for col in df.columns:
        if col not in ("league", "phase"):
            df[col] = to_number(df[col])
    return df


def pandas_measures(league, weekly, daily):
    """Same measures as in Power BI, for one league."""
    w = weekly[weekly["league"] == league]
    d = daily[daily["league"] == league]

    # Top 1% Share: sum of price per item, share of the top 1 % items
    total_per_item = w.groupby("item_key")["price_median"].sum()
    n = max(1, int(0.01 * total_per_item.size))     # computed per league
    top_share = total_per_item.nlargest(n).sum() / total_per_item.sum()

    return {
        "Median Price": w["price_median"].median(),
        "Currency Index": d["currency_index"].mean(),
        "Avg Players": d["players"].mean(),
        "Top 1% Share": top_share,
    }


def relative_diff(pbi_value, pandas_value):
    if pandas_value == 0:
        return abs(pbi_value)
    return abs(pbi_value - pandas_value) / abs(pandas_value)


def check_measures(weekly, daily):
    """Compare pbi_measures.csv with pandas. Returns True if everything is OK."""
    path = VALIDATION / "pbi_measures.csv"
    pbi = read_pbi(path).set_index("league")
    print(f"\n=== Measures ({path.name}, tolerance {TOLERANCE:.1%}) ===")
    print(f"{'league':<12}{'measure':<16}{'Power BI':>12}{'pandas':>12}{'diff':>9}")

    all_ok = True
    for league in pbi.index:
        expected = pandas_measures(league, weekly, daily)
        for measure, pandas_value in expected.items():
            pbi_value = pbi.loc[league, measure]
            diff = relative_diff(pbi_value, pandas_value)
            ok = diff < TOLERANCE
            all_ok &= ok
            print(f"{league:<12}{measure:<16}{pbi_value:>12.4f}{pandas_value:>12.4f}"
                  f"{diff:>8.3%} {'OK' if ok else 'CHECK'}")
    return all_ok


def check_volatility(daily):
    """Price Volatility: pandas and Power BI vs league_phase_summary.csv from notebook 06."""
    summary = pd.read_csv(PHASE_SUMMARY, sep=";").rename(
        columns={"League": "league", "Phase": "phase", "price_volatility": "nb06"})

    # pandas: STDEV.S = std with ddof=1 (pandas default)
    pandas_vol = (daily.groupby(["league", "phase"])["daily_change_index"]
                       .std().rename("pandas").reset_index())
    table = summary[["league", "phase", "nb06"]].merge(pandas_vol, on=["league", "phase"], how="left")

    pbi_path = VALIDATION / "pbi_volatility.csv"
    if pbi_path.exists():
        pbi = read_pbi(pbi_path).rename(columns={"Price Volatility": "power_bi"})
        table = table.merge(pbi[["league", "phase", "power_bi"]], on=["league", "phase"], how="left")
    else:
        print(f"\n(!) {pbi_path.name} not found - Power BI volatility not checked yet.")

    columns = [c for c in ("pandas", "power_bi") if c in table]
    table["ok"] = True
    for col in columns:
        table["ok"] &= (table[col] - table["nb06"]).abs() < VOL_TOLERANCE

    print(f"\n=== Price Volatility vs notebook 06 (tolerance {VOL_TOLERANCE}) ===")
    print(table.to_string(index=False, float_format=lambda x: f"{x:.7f}"))
    print(f"{table['ok'].sum()} / {len(table)} combinations OK")
    # without the Power BI export the check is not finished
    return bool(table["ok"].all()) and pbi_path.exists()


def main():
    weekly = pd.read_csv(DATA / "fact_item_weekly.csv")
    daily = pd.read_csv(DATA / "fact_daily_league.csv")

    measures_ok = check_measures(weekly, daily)
    volatility_ok = check_volatility(daily)

    print("\nRESULT:", "ALL OK" if measures_ok and volatility_ok else "SOMETHING TO CHECK")


if __name__ == "__main__":
    main()
