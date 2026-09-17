from pathlib import Path

import databento as db

from src.book.replay_book import ReplayBook
from src.features.engine.feature_engine import FeatureEngine, FeatureRow
from src.features.library.flow import bbo_ofi_increment


def apply_mbo(book: ReplayBook, msg: db.MBOMsg) -> None:
    action = msg.action

    if action == "A":
        book.add(
            order_id=msg.order_id,
            side=msg.side,
            price=msg.price,
            size=msg.size,
            ts_event=msg.ts_event
        )

    elif action == "C":
        book.cancel(
            order_id=msg.order_id,
            size=msg.size
        )

    elif action == "R":
        book.reset()

    elif action in ("T", "F", "N"):
        pass

    else:
        raise ValueError(f"Unsupported Action: {action}")


def replay_file(path):
    data = db.DBNStore.from_file(path)
    book = ReplayBook()

    last_ts_event = None
    last_sequence = None

    for msg in data:
        if not isinstance(msg, db.MBOMsg):
            continue

        apply_mbo(book, msg)

        if msg.flags & db.RecordFlags.F_LAST:
            last_ts_event = msg.ts_event
            last_sequence = msg.sequence

    return book, last_ts_event, last_sequence


def replay_features(path: str | Path, feature_engine: FeatureEngine) -> list[FeatureRow]:
    data = db.DBNStore.from_file(path)
    book = ReplayBook()

    rows: list[FeatureRow] = []

    event_messages: list[db.MBOMsg] = []

    for msg in data:
        if not isinstance(msg, db.MBOMsg):
            continue

        event_messages.append(msg)

        if not msg.flags & db.RecordFlags.F_LAST:
            continue

        event_ts = msg.ts_event

        rows.extend(
            feature_engine.emit_before(
                ts_event=msg.ts_event,
                book=book
            )
        )

        prev_bid = book.best_bid()
        prev_ask = book.best_ask()

        if prev_bid is not None and prev_ask is not None:
            prev_bbo = (
                prev_bid.price, prev_bid.total_size,
                prev_ask.price, prev_ask.total_size
            )

        else:
            prev_bbo = None

        for event_msg in event_messages:
            apply_mbo(book, event_msg)

        curr_bid = book.best_bid()
        curr_ask = book.best_ask()

        if curr_bid is not None and curr_ask is not None:
            curr_bbo = (
                curr_bid.price, curr_bid.total_size,
                curr_ask.price, curr_ask.total_size
            )

        if (
            prev_bbo is not None
            and curr_bbo is not None
            and event_ts > feature_engine.start_ts
            and event_ts <= feature_engine.end_ts
        ):
            ofi_increment = bbo_ofi_increment(
                prev_bid_price=prev_bbo[0],
                prev_bid_size=prev_bbo[1],
                prev_ask_price=prev_bbo[2],
                prev_ask_size=prev_bbo[3],

                curr_bid_price=curr_bbo[0],
                curr_bid_size=curr_bbo[1],
                curr_ask_price=curr_bbo[2],
                curr_ask_size=curr_bbo[3]
            )

            feature_engine.observe_bbo_ofi(ofi_increment)

        else:
            curr_bbo = None

        feature_engine.observe_event(
            messages=event_messages,
            ts_event=event_ts
        )

        event_messages = []

    rows.extend(feature_engine.finish(book))

    return rows
