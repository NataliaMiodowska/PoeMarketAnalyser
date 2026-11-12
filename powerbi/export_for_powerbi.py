"""Export aggregated tables for the Power BI dashboard.

Extension added after the university project. Written by Claude Code (AI assistant).

Reads the processed files created by notebooks 01-07 (folder `data/`) and writes
five small CSV files to `powerbi/data/`:

    fact_daily_league.csv    league x day
    fact_item_weekly.csv     league x week x item (all items, High confidence)
    fact_item_daily_top.csv  league x day x item (top N items per league)
    dim_item.csv             item
    dim_league.csv           league (with K-means cluster, as in notebook 08)

Usage (from the repository root):
    python powerbi/export_for_powerbi.py [DATA_DIR] [OUT_DIR]

Defaults: DATA_DIR = <repo>/data, OUT_DIR = <repo>/powerbi/data
Output format: comma separator, dot decimal, UTF-8, ISO dates (YYYY-MM-DD).
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

REPO = Path(__file__).resolve().parent.parent
DATA_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "data"
OUT_DIR = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "powerbi" / "data"

EXCLUDED_LEAGUES = {"Mirage"}  # only 7 days of data
EXPECTED_LEAGUES = 6
TOP_N_ITEMS = 300  # items per league in fact_item_daily_top
PHASES = [  # (last day of phase, name), as in notebook 06
    (7, "Launch hype"),
    (30, "Early league"),
    (70, "Mid league"),
    (10**6, "Late league"),
]
ITEM_DTYPES = {
    "League": "category",
    "Date": "category",
    "Type": "category",
    "Name": "category",
    "Value": "float32",
    "Day": "int16",
}


def check(condition: bool, message: str) -> None:
    """Stop the export when a validation fails."""
    if not condition:
        sys.exit(f"VALIDATION FAILED: {message}")
    print(f"  ok: {message}")


def read_items(path: Path) -> pd.DataFrame:
    print(f"Reading {path.name} ...")
    df = pd.read_csv(
        path, sep=";", usecols=list(ITEM_DTYPES), dtype=ITEM_DTYPES, low_memory=False
    )
    df = df[~df["League"].isin(EXCLUDED_LEAGUES)]
    df["League"] = df["League"].cat.remove_unused_categories()
    return df


def dedup_daily(df: pd.DataFrame) -> pd.DataFrame:
    """One price per (league, day, item): the median of all rows with that key."""
    out = (
        df.groupby(["Day", "Date", "Type", "Name"], observed=True)["Value"]
        .median()
        .reset_index()
    )
    out["Date"] = out["Date"].astype(str)
    out["item_key"] = out["Type"].astype(str) + "|" + out["Name"].astype(str)
    return out


def phase_of(day: int) -> tuple[str, int]:
    for order, (limit, name) in enumerate(PHASES, start=1):
        if day <= limit:
            return name, order
    raise ValueError(day)


# ---------------------------------------------------------------- items (all)
def build_market_value_and_day_map(items_path: Path):
    """market_value per league-day and the league_day <-> date map."""
    df = read_items(items_path)
    market, day_maps = [], []
    for league in sorted(df["League"].unique()):
        part = df[df["League"] == league]
        daily = dedup_daily(part)
        mv = daily.groupby(["Day", "Date"])["Value"].sum().reset_index()
        mv = mv.rename(columns={"Value": "market_value", "Day": "league_day", "Date": "date"})
        mv.insert(0, "league", league)
        market.append(mv)
        print(f"  {league}: {len(part):,} rows -> {len(daily):,} after deduplication")
    del df
    return pd.concat(market, ignore_index=True)


# ------------------------------------------------------- items (high confidence)
def build_item_tables(high_path: Path):
    df = read_items(high_path)
    weekly, top, dims = [], [], []
    for league in sorted(df["League"].unique()):
        daily = dedup_daily(df[df["League"] == league])
        daily["league"] = league

        # weekly: median of daily prices, per item and league week
        daily["league_week"] = (daily["Day"] - 1) // 7 + 1
        daily["week_start"] = daily.groupby("league_week")["Date"].transform("min")
        w = (
            daily.groupby(["league", "league_week", "week_start", "item_key"])["Value"]
            .median()
            .reset_index()
            .rename(columns={"Value": "price_median"})
        )
        weekly.append(w)

        # daily: top N items by total value
        totals = daily.groupby("item_key")["Value"].sum().nlargest(TOP_N_ITEMS)
        t = daily[daily["item_key"].isin(totals.index)][
            ["league", "Date", "Day", "item_key", "Value"]
        ].rename(
            columns={"Date": "date", "Day": "league_day", "Value": "price_chaos"}
        )
        top.append(t)

        dims.append(daily[["item_key", "Type", "Name"]].drop_duplicates("item_key"))
        print(f"  {league}: {len(w):,} weekly rows, {len(t):,} daily top rows")
    del df
    weekly = pd.concat(weekly, ignore_index=True)
    top = pd.concat(top, ignore_index=True)
    dim = pd.concat(dims).drop_duplicates("item_key")
    dim = dim.rename(columns={"Name": "item_name", "Type": "category"})
    dim["item_name"] = dim["item_name"].astype(str)
    dim["category"] = dim["category"].astype(str)
    return weekly, top, dim.sort_values("item_key").reset_index(drop=True)


# ------------------------------------------------------------------- clusters
def build_clusters(indicators_path: Path) -> pd.DataFrame:
    """Same procedure as notebook 08: scale -> PCA -> 3 PCs -> KMeans(4, rs=50)."""
    ind = pd.read_csv(indicators_path, sep=";", low_memory=False)
    ind = ind[~ind["League"].isin(EXCLUDED_LEAGUES)].reset_index(drop=True)
    x = StandardScaler().fit_transform(ind.drop(columns=["League"]))
    x_pca = PCA().fit_transform(x)[:, :3]
    labels = KMeans(n_clusters=4, random_state=50).fit_predict(x_pca)
    return pd.DataFrame(
        {"league": ind["League"], "cluster": [f"Cluster {k + 1}" for k in labels]}
    )


def main() -> None:
    items_dir = DATA_DIR / "items_data_processed"
    currency_dir = DATA_DIR / "currency_data_processed"
    players_path = DATA_DIR / "players_data_processed" / "players_processed.csv"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- items and market value
    market = build_market_value_and_day_map(items_dir / "items_processed_day.csv")
    weekly, top, dim_item = build_item_tables(items_dir / "high_conf_items_processed_day.csv")

    # --- daily league table
    day_map = market[["league", "league_day", "date"]]
    ci = pd.read_csv(currency_dir / "currency_index.csv", sep=";").rename(
        columns={"League": "league", "Day": "league_day"}
    )
    ci = ci[~ci["league"].isin(EXCLUDED_LEAGUES)]

    # the currency files must use the same day numbering as the item files
    cur = pd.read_csv(
        currency_dir / "currency_processed_day.csv",
        sep=";",
        usecols=["League", "Date", "Day"],
    ).drop_duplicates()
    cur = cur[~cur["League"].isin(EXCLUDED_LEAGUES)].rename(
        columns={"League": "league", "Date": "date", "Day": "league_day"}
    )
    print("Validation of day numbering:")
    merged = cur.merge(day_map, on=["league", "league_day"], how="outer", indicator=True)
    check(
        (merged["_merge"] == "both").all() and (merged["date_x"] == merged["date_y"]).all(),
        "currency Day -> Date map equals the item Day -> Date map",
    )

    daily = market.merge(ci, on=["league", "league_day"], how="left")
    daily = daily.sort_values(["league", "league_day"]).reset_index(drop=True)
    daily["daily_change_index"] = (
        daily.groupby("league")["currency_index"].pct_change().fillna(0.0)
    )
    daily[["phase", "phase_order"]] = daily["league_day"].apply(
        lambda d: pd.Series(phase_of(int(d)))
    )

    if players_path.exists():
        pl = pd.read_csv(players_path, sep=";").rename(
            columns={"League": "league", "Date": "date", "Players": "players"}
        )
        daily = daily.merge(pl[["league", "date", "players"]], on=["league", "date"], how="left")
        first = daily.groupby("league")["players"].transform(
            lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan
        )
        daily["players_norm"] = daily["players"] / first
    else:
        print(f"WARNING: {players_path} not found - players columns will be empty.")
        daily["players"] = np.nan
        daily["players_norm"] = np.nan

    daily = daily[
        [
            "league", "date", "league_day", "phase", "phase_order",
            "currency_index", "daily_change_index", "players", "players_norm",
            "market_value",
        ]
    ]

    # --- league dimension
    dim_league = (
        daily.groupby("league")
        .agg(start_date=("date", "min"), end_date=("date", "max"), n_days=("league_day", "max"))
        .reset_index()
        .sort_values("start_date")
    )
    dim_league = dim_league.merge(build_clusters(items_dir / "league_economic_indicators.csv"),
                                  on="league", how="left")

    # --- validations
    print("Validation of output tables:")
    today = date.today().isoformat()
    check(daily["league"].nunique() == EXPECTED_LEAGUES, f"{EXPECTED_LEAGUES} leagues in fact_daily_league")
    for name, frame, key in [
        ("fact_daily_league", daily, ["league", "date"]),
        ("fact_item_weekly", weekly, ["league", "week_start", "item_key"]),
        ("fact_item_daily_top", top, ["league", "date", "item_key"]),
        ("dim_item", dim_item, ["item_key"]),
        ("dim_league", dim_league, ["league"]),
    ]:
        check(not frame.duplicated(key).any(), f"no duplicate keys in {name}")
        check(not frame[key].isna().any().any(), f"no missing key values in {name}")
    check(daily["date"].max() <= today and top["date"].max() <= today,
          "no dates in the future")
    check((weekly["price_median"] > 0).all() and (top["price_chaos"] > 0).all(),
          "all prices > 0")
    check((daily["market_value"] > 0).all(), "market_value > 0")
    check(daily["currency_index"].notna().all(), "currency_index present for every league-day")
    for league, g in daily.groupby("league"):
        days = g["league_day"].to_numpy()
        check((days == np.arange(1, len(days) + 1)).all(), f"{league}: league_day continuous 1..{len(days)}")
    known = set(dim_item["item_key"])
    check(set(weekly["item_key"]) <= known and set(top["item_key"]) <= known,
          "every item_key in the facts exists in dim_item")
    check(dim_league["cluster"].nunique() == 4 and dim_league["cluster"].notna().all(),
          "4 clusters, every league assigned")

    # --- write
    daily["currency_index"] = daily["currency_index"].round(8)
    daily["daily_change_index"] = daily["daily_change_index"].round(8)
    daily["players_norm"] = daily["players_norm"].round(8)
    daily["market_value"] = daily["market_value"].round(2)
    daily["players"] = daily["players"].round(0).astype("Int64")
    weekly["price_median"] = weekly["price_median"].round(4)
    top["price_chaos"] = top["price_chaos"].round(4)

    outputs = {
        "fact_daily_league.csv": daily,
        "fact_item_weekly.csv": weekly,
        "fact_item_daily_top.csv": top,
        "dim_item.csv": dim_item,
        "dim_league.csv": dim_league,
    }
    print("Written files:")
    for fname, frame in outputs.items():
        path = OUT_DIR / fname
        frame.to_csv(path, index=False, encoding="utf-8")
        print(f"  {fname}: {len(frame):,} rows, {path.stat().st_size / 1e6:.1f} MB")
    print("\nClusters:")
    print(dim_league[["league", "cluster"]].to_string(index=False))


if __name__ == "__main__":
    main()
