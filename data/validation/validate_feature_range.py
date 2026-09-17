import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from data.acquisition.sessions import TradingSession, get_trading_sessions


ROOT = Path(__file__).resolve().parents[2]

SAMPLE_INTERVAL = pd.Timedelta(milliseconds=100)

HORIZONS = {
    "500ms": 5,
    "1s": 10,
    "2s": 20,
    "5s": 50
}

TARGET_COLUMNS = {
    "500ms": (
        "target_return_500ms",
        "target_spread_move_500ms"
    ),
    "1s": (
        "target_return_1s",
        "target_spread_move_1s"
    ),
    "2s": (
        "target_return_2s",
        "target_spread_move_2s"
    ),
    "5s": (
        "target_return_5s",
        "target_spread_move_5s"
    )
}

CORE_COLUMNS = [
    "ts_event",
    "best_bid",
    "best_ask",
    "mid",
    "spread",
    "microprice",
    "bid_depth_1",
    "ask_depth_1",
    "bid_depth_5",
    "ask_depth_5",
    "bid_depth_10",
    "ask_depth_10",
    "imbalance_1",
    "imbalance_5",
    "imbalance_10",
    "bid_add_volume",
    "ask_add_volume",
    "bid_cancel_volume",
    "ask_cancel_volume",
    "buy_trade_volume",
    "sell_trade_volume",
    "bid_add_count",
    "ask_add_count",
    "bid_cancel_count",
    "ask_cancel_count",
    "buy_fill_count",
    "sell_fill_count",
    "bbo_ofi",
    "add_imbalance",
    "cancel_imbalance",
    "trade_imbalance",
    "book_pressure",
    "normalized_book_pressure",
    "total_add_volume",
    "total_cancel_volume",
    "total_trade_volume",
    "total_event_count"
]

WARMUP_COLUMNS = {
    "bbo_ofi_500ms": 4,
    "bbo_ofi_1s": 9,
    "bbo_ofi_5s": 49,
    "mid_return_500ms": 5,
    "mid_return_1s": 10,
    "mid_return_5s": 50,
    "volatility_500ms": 5,
    "volatility_1s": 10,
    "volatility_5s": 50
}


def get_feature_path(
    symbol: str,
    session: TradingSession
) -> Path:
    date_string = session.date.isoformat()

    return (
        ROOT
        / "data"
        / "features"
        / symbol
        / f"{symbol}_{date_string}_100ms.parquet"
    )


def validate_columns(
    df: pd.DataFrame,
    date_string: str
) -> None:
    missing_core = [
        column
        for column in CORE_COLUMNS
        if column not in df.columns
    ]

    if missing_core:
        raise AssertionError(
            f"{date_string}: missing core columns: "
            f"{missing_core}"
        )

    required_targets = [
        column
        for columns in TARGET_COLUMNS.values()
        for column in columns
    ]

    missing_targets = [
        column
        for column in required_targets
        if column not in df.columns
    ]

    if missing_targets:
        raise AssertionError(
            f"{date_string}: missing target columns: "
            f"{missing_targets}"
        )


def validate_timing(
    df: pd.DataFrame,
    session: TradingSession
) -> None:
    date_string = session.date.isoformat()

    timestamps = pd.to_datetime(
        df["ts_event"],
        utc=True
    )

    expected_rows = int(
        (session.market_close - session.market_open)
        / SAMPLE_INTERVAL
    )

    if len(df) != expected_rows:
        raise AssertionError(
            f"{date_string}: expected "
            f"{expected_rows:,} rows, "
            f"found {len(df):,}"
        )

    expected_first = (
        session.market_open
        + SAMPLE_INTERVAL
    )

    if timestamps.iloc[0] != expected_first:
        raise AssertionError(
            f"{date_string}: incorrect first timestamp: "
            f"{timestamps.iloc[0]} != {expected_first}"
        )

    if timestamps.iloc[-1] != session.market_close:
        raise AssertionError(
            f"{date_string}: incorrect final timestamp: "
            f"{timestamps.iloc[-1]} != "
            f"{session.market_close}"
        )

    differences = (
        timestamps
        .diff()
        .iloc[1:]
    )

    if not (
        differences == SAMPLE_INTERVAL
    ).all():
        raise AssertionError(
            f"{date_string}: timestamps are not "
            f"exactly 100ms apart"
        )


def validate_core_values(
    df: pd.DataFrame,
    date_string: str
) -> None:
    core_values = df[CORE_COLUMNS]

    if core_values.isna().any().any():
        bad_columns = (
            core_values
            .columns[
                core_values.isna().any()
            ]
            .tolist()
        )

        raise AssertionError(
            f"{date_string}: unexpected NaNs "
            f"in core columns: {bad_columns}"
        )

    numeric = df.select_dtypes(
        include=[np.number]
    )

    if np.isinf(
        numeric.to_numpy()
    ).any():
        raise AssertionError(
            f"{date_string}: infinite numeric values found"
        )

    if not (
        df["best_bid"] < df["best_ask"]
    ).all():
        raise AssertionError(
            f"{date_string}: locked or crossed book found"
        )

    if not (
        df["spread"] > 0
    ).all():
        raise AssertionError(
            f"{date_string}: non-positive spread found"
        )


def validate_rolling_warmup(
    df: pd.DataFrame,
    date_string: str
) -> None:
    for column, expected_nan_count in WARMUP_COLUMNS.items():
        if column not in df.columns:
            raise AssertionError(
                f"{date_string}: missing rolling column "
                f"{column}"
            )

        actual_nan_count = int(
            df[column].isna().sum()
        )

        if actual_nan_count != expected_nan_count:
            raise AssertionError(
                f"{date_string}: {column} expected "
                f"{expected_nan_count} warmup NaNs, "
                f"found {actual_nan_count}"
            )


def validate_bounded_features(
    df: pd.DataFrame,
    date_string: str
) -> None:
    bounded_columns = [
        column
        for column in df.columns
        if (
            "imbalance" in column
            or column.startswith(
                "normalized_book_pressure"
            )
        )
    ]

    for column in bounded_columns:
        values = df[column].dropna()

        if (
            (values < -1.0).any()
            or (values > 1.0).any()
        ):
            raise AssertionError(
                f"{date_string}: {column} "
                f"outside [-1, 1]"
            )

    if "microprice_skew" not in df.columns:
        raise AssertionError(
            f"{date_string}: missing microprice_skew"
        )

    skew = (
        df["microprice_skew"]
        .dropna()
    )

    if (
        (skew < -0.5).any()
        or (skew > 0.5).any()
    ):
        raise AssertionError(
            f"{date_string}: microprice_skew "
            f"outside [-0.5, 0.5]"
        )


def validate_targets(
    df: pd.DataFrame,
    date_string: str
) -> None:
    for label, horizon in HORIZONS.items():
        return_column, spread_column = (
            TARGET_COLUMNS[label]
        )

        expected_nan_mask = np.zeros(
            len(df),
            dtype=bool
        )

        expected_nan_mask[-horizon:] = True

        future_mid = df["mid"].shift(
            -horizon
        )

        expected_return = (
            future_mid / df["mid"] - 1
        )

        expected_spread_move = (
            (future_mid - df["mid"])
            / df["spread"]
        )

        expected_values = {
            return_column: expected_return,
            spread_column: expected_spread_move
        }

        for column, expected in expected_values.items():
            actual = df[column]

            actual_nan_mask = (
                actual
                .isna()
                .to_numpy()
            )

            if not np.array_equal(
                actual_nan_mask,
                expected_nan_mask
            ):
                raise AssertionError(
                    f"{date_string}: incorrect "
                    f"EOD NaNs for {column}"
                )

            valid = ~expected.isna()

            if not np.allclose(
                actual[valid].to_numpy(),
                expected[valid].to_numpy(),
                rtol=1e-12,
                atol=1e-15
            ):
                raise AssertionError(
                    f"{date_string}: target formula "
                    f"mismatch for {column}"
                )


def validate_day(
    symbol: str,
    session: TradingSession
) -> None:
    date_string = session.date.isoformat()

    path = get_feature_path(
        symbol,
        session
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Feature file not found: {path}"
        )

    print(
        f"Validating {symbol} {date_string}..."
    )

    df = pd.read_parquet(
        path
    )

    validate_columns(
        df,
        date_string
    )

    validate_timing(
        df,
        session
    )

    validate_core_values(
        df,
        date_string
    )

    validate_rolling_warmup(
        df,
        date_string
    )

    validate_bounded_features(
        df,
        date_string
    )

    validate_targets(
        df,
        date_string
    )

    print(
        f"{date_string}: PASS "
        f"({len(df):,} rows)"
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--symbol",
        default="NVDA"
    )

    parser.add_argument(
        "--start",
        required=True
    )

    parser.add_argument(
        "--end",
        required=True
    )

    args = parser.parse_args()

    symbol = args.symbol.upper()

    sessions = get_trading_sessions(
        args.start,
        args.end
    )

    if len(sessions) == 0:
        raise ValueError(
            "No trading sessions found "
            "in requested range"
        )

    print()
    print("=" * 70)
    print("FEATURE RANGE VALIDATION")
    print("=" * 70)

    print(f"Symbol: {symbol}")
    print(f"Sessions: {len(sessions)}")

    print()

    for session in sessions:
        validate_day(
            symbol,
            session
        )

    print()
    print("=" * 70)
    print(
        f"ALL {len(sessions)} FEATURE FILES PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
    