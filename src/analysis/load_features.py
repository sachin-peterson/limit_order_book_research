from pathlib import Path

import pandas as pd

from data.acquisition.sessions import get_trading_sessions


ROOT = Path(__file__).resolve().parents[2]


def load_feature_range(
    symbol: str,
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    symbol = symbol.upper()

    sessions = get_trading_sessions(
        start_date,
        end_date
    )

    if len(sessions) == 0:
        raise ValueError(
            "No trading sessions found in requested range"
        )

    frames: list[pd.DataFrame] = []

    for session in sessions:
        date_string = session.date.isoformat()

        path = (
            ROOT
            / "data"
            / "features"
            / symbol
            / f"{symbol}_{date_string}_100ms.parquet"
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Feature file not found: {path}"
            )

        df = pd.read_parquet(
            path
        )

        df["ts_event"] = pd.to_datetime(
            df["ts_event"],
            utc=True
        )

        df.insert(
            0,
            "date",
            date_string
        )

        frames.append(
            df
        )

    result = pd.concat(
        frames,
        ignore_index=True
    )

    result = result.sort_values(
        "ts_event"
    ).reset_index(
        drop=True
    )

    return result
