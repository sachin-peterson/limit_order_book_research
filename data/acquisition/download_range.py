import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import databento as db

from data.acquisition.manifest import (
    is_complete,
    load_manifest,
    update_manifest
)
from data.acquisition.sessions import TradingSession, get_trading_sessions


ROOT = Path(__file__).resolve().parents[2]

DATASET = "XNAS.ITCH"
SCHEMA = "mbo"

MAX_RETRIES = 3


def get_paths(symbol: str, session: TradingSession) -> tuple[Path, Path]:
    raw_dir = (
        ROOT
        / "data"
        / "raw"
        / symbol
        / SCHEMA
    )

    raw_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    date_string = session.date.isoformat()

    final_path = raw_dir / f"{symbol}_{date_string}_{SCHEMA}.dbn.zst"
    temp_path = raw_dir / f"{symbol}_{date_string}_{SCHEMA}.tmp.dbn.zst"

    return final_path, temp_path


def validate_dbn(path: Path) -> None:
    if not path.exists():
        raise ValueError(f"File does not exist: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"File is empty: {path}")

    store = db.DBNStore.from_file(path)
    first_record = next(iter(store), None)

    if first_record is None:
        raise ValueError(f"No records found: {path}")


def estimate_cost(
    client: db.Historical,
    symbol: str,
    session: TradingSession
) -> float:
    return client.metadata.get_cost(
        dataset=DATASET,
        symbols=symbol,
        schema=SCHEMA,
        start=session.request_start,
        end=session.market_close
    )


def register_existing_file(
    symbol: str,
    session: TradingSession,
    manifest_path: Path,
    final_path: Path
) -> None:
    date_string = session.date.isoformat()

    validate_dbn(final_path)

    update_manifest(
        manifest_path,
        {
            "date": date_string,
            "symbol": symbol,
            "dataset": DATASET,
            "schema": SCHEMA,
            "start": str(session.request_start),
            "end": str(session.market_close),
            "status": "complete",
            "path": str(final_path.relative_to(ROOT)),
            "bytes": final_path.stat().st_size,
            "estimated_cost": "",
            "downloaded_at": "",
            "error": ""
        }
    )

    print(
        f"{date_string} exists and was added to manifest"
    )


def download_session(
    client: db.Historical,
    symbol: str,
    session: TradingSession,
    manifest_path: Path,
    estimated_cost: float
) -> None:
    date_string = session.date.isoformat()

    final_path, temp_path = get_paths(
        symbol,
        session
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if temp_path.exists():
                temp_path.unlink()

            print(
                f"{date_string} downloading "
                f"(attempt {attempt}/{MAX_RETRIES})"
            )

            client.timeseries.get_range(
                dataset=DATASET,
                symbols=symbol,
                schema=SCHEMA,
                start=session.request_start,
                end=session.market_close,
                path=temp_path
            )

            validate_dbn(temp_path)

            temp_path.replace(final_path)

            update_manifest(
                manifest_path,
                {
                    "date": date_string,
                    "symbol": symbol,
                    "dataset": DATASET,
                    "schema": SCHEMA,
                    "start": str(session.request_start),
                    "end": str(session.market_close),
                    "status": "complete",
                    "path": str(final_path.relative_to(ROOT)),
                    "bytes": final_path.stat().st_size,
                    "estimated_cost": estimated_cost,
                    "downloaded_at": datetime.now(timezone.utc).isoformat(),
                    "error": ""
                }
            )

            print(
                f"{date_string} complete "
                f"({final_path.stat().st_size / 1_000_000:.1f} MB)"
            )

            return

        except Exception as error:
            print(
                f"{date_string} failed: {error}"
            )

            if temp_path.exists():
                temp_path.unlink()

            if attempt < MAX_RETRIES:
                wait_seconds = 2 ** attempt

                print(
                    f"Retrying in {wait_seconds}s"
                )

                time.sleep(wait_seconds)

            else:
                update_manifest(
                    manifest_path,
                    {
                        "date": date_string,
                        "symbol": symbol,
                        "dataset": DATASET,
                        "schema": SCHEMA,
                        "start": str(session.request_start),
                        "end": str(session.market_close),
                        "status": "failed",
                        "path": "",
                        "bytes": 0,
                        "estimated_cost": estimated_cost,
                        "downloaded_at": "",
                        "error": str(error)
                    }
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

    parser.add_argument(
        "--dry-run",
        action="store_true"
    )

    parser.add_argument(
        "--max-cost",
        type=float
    )

    args = parser.parse_args()

    symbol = args.symbol.upper()

    manifest_path = (
        ROOT
        / "data"
        / "manifests"
        / f"{symbol}_{SCHEMA}.csv"
    )

    sessions = get_trading_sessions(
        args.start,
        args.end
    )

    manifest = load_manifest(
        manifest_path
    )

    missing_sessions = []

    for session in sessions:
        date_string = session.date.isoformat()

        final_path, _ = get_paths(
            symbol,
            session
        )

        if is_complete(
            manifest,
            date_string,
            symbol,
            DATASET,
            SCHEMA
        ) and final_path.exists():
            continue

        if final_path.exists():
            register_existing_file(
                symbol,
                session,
                manifest_path,
                final_path
            )
            continue

        missing_sessions.append(
            session
        )

    print()
    print(f"Symbol: {symbol}")
    print(f"Sessions: {len(sessions)}")
    print(f"Already complete: {len(sessions) - len(missing_sessions)}")
    print(f"Missing: {len(missing_sessions)}")

    if not missing_sessions:
        print("Nothing to download.")
        return

    client = db.Historical()

    costs = {}

    print()
    print("Estimating Databento cost...")

    for session in missing_sessions:
        cost = estimate_cost(
            client,
            symbol,
            session
        )

        costs[session.date] = cost

        print(
            f"{session.date}: ${cost:.4f}"
        )

    total_cost = sum(
        costs.values()
    )

    print()
    print(
        f"Estimated total cost: ${total_cost:.2f}"
    )

    if args.dry_run:
        print(
            "Dry run only. No data downloaded."
        )
        return

    if args.max_cost is None:
        raise ValueError(
            "Provide --max-cost before downloading."
        )

    if total_cost > args.max_cost:
        raise ValueError(
            f"Estimated cost ${total_cost:.2f} "
            f"exceeds --max-cost ${args.max_cost:.2f}"
        )

    print()
    print("Starting downloads...")

    for session in missing_sessions:
        download_session(
            client=client,
            symbol=symbol,
            session=session,
            manifest_path=manifest_path,
            estimated_cost=costs[session.date]
        )

    print()
    print("Download range complete.")


if __name__ == "__main__":
    main()
    