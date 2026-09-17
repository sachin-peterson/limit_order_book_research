import argparse
from pathlib import Path

import databento as db

from data.acquisition.sessions import TradingSession, get_trading_sessions
from src.book.replay_book import ReplayBook
from src.replay.replay_file import apply_mbo


ROOT = Path(__file__).resolve().parents[2]


def get_mbo_path(symbol: str, session: TradingSession) -> Path:
    date_string = session.date.isoformat()

    return (
        ROOT
        / "data"
        / "raw"
        / symbol
        / "mbo"
        / f"{symbol}_{date_string}_mbo.dbn.zst"
    )


def get_mbp10_path(symbol: str, session: TradingSession) -> Path:
    date_string = session.date.isoformat()

    validation_dir = (
        ROOT
        / "data"
        / "raw"
        / symbol
        / "mbp10"
    )

    matches = list(
        validation_dir.glob(
            f"{symbol}_{date_string}_*_mbp10.dbn.zst"
        )
    )

    if len(matches) == 0:
        raise FileNotFoundError(
            f"No MBP-10 validation file found for {date_string}"
        )

    if len(matches) > 1:
        raise ValueError(
            f"Multiple MBP-10 validation files found for {date_string}: "
            f"{matches}"
        )

    return matches[0]


def replay_mbo(path: Path) -> ReplayBook:
    if not path.exists():
        raise FileNotFoundError(
            f"MBO file not found: {path}"
        )

    book = ReplayBook()
    store = db.DBNStore.from_file(path)

    record_count = 0

    for record in store:
        apply_mbo(book, record)
        record_count += 1

    if record_count == 0:
        raise ValueError(
            f"MBO file contains no records: {path}"
        )

    print(
        f"Replayed {record_count:,} MBO records."
    )

    return book


def get_final_mbp10(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            f"MBP-10 file not found: {path}"
        )

    store = db.DBNStore.from_file(path)

    final_record = None
    record_count = 0

    for record in store:
        final_record = record
        record_count += 1

    if final_record is None:
        raise ValueError(
            f"MBP-10 file contains no records: {path}"
        )

    print(
        f"Loaded {record_count:,} MBP-10 records."
    )

    return final_record


def validate_level(
    date_string: str,
    side: str,
    level_number: int,
    actual_price: int,
    actual_size: int,
    actual_count: int,
    expected_price: int,
    expected_size: int,
    expected_count: int
) -> None:
    prefix = (
        f"{date_string} "
        f"{side} "
        f"L{level_number}"
    )

    if actual_price != expected_price:
        raise AssertionError(
            f"{prefix} price mismatch: "
            f"book={actual_price}, "
            f"MBP10={expected_price}"
        )

    if actual_size != expected_size:
        raise AssertionError(
            f"{prefix} size mismatch: "
            f"book={actual_size}, "
            f"MBP10={expected_size}"
        )

    if actual_count != expected_count:
        raise AssertionError(
            f"{prefix} count mismatch: "
            f"book={actual_count}, "
            f"MBP10={expected_count}"
        )


def validate_day(
    symbol: str,
    session: TradingSession
) -> dict[str, int | str]:
    date_string = session.date.isoformat()

    print()
    print("=" * 70)
    print(f"VALIDATING {symbol} {date_string}")
    print("=" * 70)

    mbo_path = get_mbo_path(
        symbol,
        session
    )

    mbp10_path = get_mbp10_path(
        symbol,
        session
    )

    print(
        f"MBO:   {mbo_path.relative_to(ROOT)}"
    )

    print(
        f"MBP10: {mbp10_path.relative_to(ROOT)}"
    )

    print()
    print("Replaying MBO...")

    book = replay_mbo(
        mbo_path
    )

    best_bid = book.best_bid()
    best_ask = book.best_ask()

    if best_bid is None:
        raise AssertionError(
            f"{date_string}: reconstructed book has no best bid"
        )

    if best_ask is None:
        raise AssertionError(
            f"{date_string}: reconstructed book has no best ask"
        )

    if best_bid.price >= best_ask.price:
        raise AssertionError(
            f"{date_string}: reconstructed book is locked or crossed: "
            f"bid={best_bid.price}, "
            f"ask={best_ask.price}"
        )

    reconstructed_bids, reconstructed_asks = book.top_levels(10)

    if len(reconstructed_bids) < 10:
        raise AssertionError(
            f"{date_string}: reconstructed book has only "
            f"{len(reconstructed_bids)} bid levels"
        )

    if len(reconstructed_asks) < 10:
        raise AssertionError(
            f"{date_string}: reconstructed book has only "
            f"{len(reconstructed_asks)} ask levels"
        )

    print()
    print("Loading final MBP-10 snapshot...")

    mbp10 = get_final_mbp10(
        mbp10_path
    )

    if len(mbp10.levels) < 10:
        raise AssertionError(
            f"{date_string}: MBP-10 snapshot has fewer than 10 levels"
        )

    print()
    print("Comparing top 10 levels...")

    for i in range(10):
        book_bid = reconstructed_bids[i]
        book_ask = reconstructed_asks[i]
        reference = mbp10.levels[i]

        validate_level(
            date_string=date_string,
            side="BID",
            level_number=i + 1,
            actual_price=int(book_bid.price),
            actual_size=int(book_bid.total_size),
            actual_count=int(book_bid.order_count),
            expected_price=int(reference.bid_px),
            expected_size=int(reference.bid_sz),
            expected_count=int(reference.bid_ct)
        )

        validate_level(
            date_string=date_string,
            side="ASK",
            level_number=i + 1,
            actual_price=int(book_ask.price),
            actual_size=int(book_ask.total_size),
            actual_count=int(book_ask.order_count),
            expected_price=int(reference.ask_px),
            expected_size=int(reference.ask_sz),
            expected_count=int(reference.ask_ct)
        )

    print(
        "Top 10 price / size / count MATCH."
    )

    print()
    print(
        f"Best bid: "
        f"${best_bid.price / db.FIXED_PRICE_SCALE:.2f} "
        f"x {best_bid.total_size} "
        f"({best_bid.order_count} orders)"
    )

    print(
        f"Best ask: "
        f"${best_ask.price / db.FIXED_PRICE_SCALE:.2f} "
        f"x {best_ask.total_size} "
        f"({best_ask.order_count} orders)"
    )

    print(
        f"Active orders: {len(book.order_index):,}"
    )

    print(
        f"Bid levels: {len(book.bids):,}"
    )

    print(
        f"Ask levels: {len(book.asks):,}"
    )

    print()
    print(
        f"{date_string} PASS"
    )

    return {
        "date": date_string,
        "active_orders": len(book.order_index),
        "bid_levels": len(book.bids),
        "ask_levels": len(book.asks)
    }


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
            "No trading sessions found in requested range"
        )

    print()
    print("=" * 70)
    print("MBO RECONSTRUCTION VALIDATION")
    print("=" * 70)

    print(
        f"Symbol: {symbol}"
    )

    print(
        f"Start: {args.start}"
    )

    print(
        f"End: {args.end}"
    )

    print(
        f"Sessions: {len(sessions)}"
    )

    results = []

    for session in sessions:
        result = validate_day(
            symbol,
            session
        )

        results.append(
            result
        )

    print()
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    for result in results:
        print(
            f"{result['date']}  "
            f"PASS  "
            f"orders={result['active_orders']:,}  "
            f"bid_levels={result['bid_levels']:,}  "
            f"ask_levels={result['ask_levels']:,}"
        )

    print()
    print("=" * 70)
    print(
        f"ALL {len(results)} TRADING DAYS PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()