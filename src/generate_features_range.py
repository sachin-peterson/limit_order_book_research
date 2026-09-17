import argparse

from data.acquisition.sessions import get_trading_sessions
from src.generate_features_day import generate_features_day


def generate_features_range(
    symbol: str,
    start_date: str,
    end_date: str,
    overwrite: bool = False
) -> None:
    symbol = symbol.upper()

    sessions = get_trading_sessions(
        start_date,
        end_date
    )

    if len(sessions) == 0:
        raise ValueError(
            "No trading sessions found in requested range"
        )

    print()
    print("=" * 70)
    print("FEATURE GENERATION")
    print("=" * 70)

    print(f"Symbol: {symbol}")
    print(f"Start: {start_date}")
    print(f"End: {end_date}")
    print(f"Sessions: {len(sessions)}")

    print()

    for i, session in enumerate(sessions, start=1):
        date_string = session.date.isoformat()

        print(
            f"[{i}/{len(sessions)}] "
            f"{symbol} {date_string}"
        )

        generate_features_day(
            symbol=symbol,
            date_string=date_string,
            overwrite=overwrite
        )

    print()
    print("=" * 70)
    print(
        f"ALL {len(sessions)} TRADING DAYS COMPLETE"
    )
    print("=" * 70)


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

    parser.add_argument(
        "--overwrite",
        action="store_true"
    )

    args = parser.parse_args()

    generate_features_range(
        symbol=args.symbol,
        start_date=args.start,
        end_date=args.end,
        overwrite=args.overwrite
    )


if __name__ == "__main__":
    main()
