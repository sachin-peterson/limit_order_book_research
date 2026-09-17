from pathlib import Path

import pandas as pd


MANIFEST_COLUMNS = [
    "date",
    "symbol",
    "dataset",
    "schema",
    "start",
    "end",
    "status",
    "path",
    "bytes",
    "estimated_cost",
    "downloaded_at",
    "error"
]


def load_manifest(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=MANIFEST_COLUMNS)

    return pd.read_csv(path)


def update_manifest(path: Path, record: dict) -> None:
    df = load_manifest(path)

    key = (
        (df["date"] == record["date"])
        & (df["symbol"] == record["symbol"])
        & (df["dataset"] == record["dataset"])
        & (df["schema"] == record["schema"])
    )

    if key.any():
        for column, value in record.items():
            df.loc[key, column] = value
    else:
        df = pd.concat(
            [df, pd.DataFrame([record])],
            ignore_index=True
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temp_path = path.with_suffix(".tmp.csv")

    df.to_csv(
        temp_path,
        index=False
    )

    temp_path.replace(path)


def is_complete(
    manifest: pd.DataFrame,
    date: str,
    symbol: str,
    dataset: str,
    schema: str
) -> bool:
    if manifest.empty:
        return False

    rows = manifest[
        (manifest["date"] == date)
        & (manifest["symbol"] == symbol)
        & (manifest["dataset"] == dataset)
        & (manifest["schema"] == schema)
    ]

    if rows.empty:
        return False

    return rows.iloc[-1]["status"] == "complete"
