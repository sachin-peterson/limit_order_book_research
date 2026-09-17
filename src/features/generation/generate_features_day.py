import argparse
from pathlib import Path

import pandas as pd

from data.acquisition.sessions import get_trading_sessions

from src.features.engine.feature_engine import FeatureEngine
from src.features.library.rolling import add_rolling_features
from src.features.utils import ns_from_ms
from src.replay.replay_file import replay_features
from src.targets.targets import add_targets


ROOT = Path(__file__).resolve().parents[1]


def generate_features_day(
    symbol: str,
    date_string: str,
    overwrite: bool = False
) -> Path:
    symbol = symbol.upper()

    sessions = get_trading_sessions(
        date_string,
        date_string
    )

    if len(sessions) != 1:
        raise ValueError(
            f"{date_string} is not a valid trading session"
        )

    session = sessions[0]
    date_string = session.date.isoformat()

    mbo_path = (
        ROOT
        / "data"
        / "raw"
        / symbol
        / "mbo"
        / f"{symbol}_{date_string}_mbo.dbn.zst"
    )

    output_dir = (
        ROOT
        / "data"
        / "features"
        / symbol
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        output_dir
        / f"{symbol}_{date_string}_100ms.parquet"
    )

    temp_path = (
        output_dir
        / f"{symbol}_{date_string}_100ms.tmp.parquet"
    )

    if output_path.exists() and not overwrite:
        print(
            f"{date_string}: exists -> skipping"
        )
        return output_path

    if not mbo_path.exists():
        raise FileNotFoundError(
            f"MBO file not found: {mbo_path}"
        )

    if temp_path.exists():
        temp_path.unlink()

    start_ts = session.market_open.value
    end_ts = session.market_close.value

    feature_engine = FeatureEngine(
        sample_interval_ns=ns_from_ms(100),
        start_ts=start_ts,
        end_ts=end_ts
    )

    rows = replay_features(
        path=mbo_path,
        feature_engine=feature_engine
    )

    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError(
            f"No feature rows generated for {symbol} {date_string}"
        )

    df = add_rolling_features(df)
    df = add_targets(df)

    df["ts_event"] = pd.to_datetime(
        df["ts_event"],
        unit="ns",
        utc=True
    )

    try:
        df.to_parquet(
            temp_path,
            index=False
        )

        temp_path.replace(
            output_path
        )

    except Exception:
        if temp_path.exists():
            temp_path.unlink()

        raise

    print(
        f"{date_string}: "
        f"{len(df):,} rows -> "
        f"{output_path.relative_to(ROOT)}"
    )

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbol",
        default="NVDA"
    )

    parser.add_argument(
        "--date",
        required=True
    )

    parser.add_argument(
        "--overwrite",
        action="store_true"
    )

    args = parser.parse_args()

    generate_features_day(
        symbol=args.symbol,
        date_string=args.date,
        overwrite=args.overwrite
    )


if __name__ == "__main__":
    main()
