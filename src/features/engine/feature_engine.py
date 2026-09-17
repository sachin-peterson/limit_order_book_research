import databento as db

from src.book.replay_book import ReplayBook
from src.features.engine.flow_accumulator import FlowAccumulator

from src.features.library.state import (
    depth, 
    imbalance, 
    microprice, 
    mid_price, 
    spread
)

from src.features.library.flow import (
    add_imbalance,
    cancel_imbalance,
    trade_imbalance,
    book_pressure,
    book_pressure_normalized,
    total_add_volume,
    total_cancel_volume,
    total_trade_volume,
    total_event_count
)

FeatureRow = dict[str, int | float | None]


class FeatureEngine:
    def __init__(self, sample_interval_ns: int, start_ts: int, end_ts: int) -> None:
        if sample_interval_ns <= 0:
            raise ValueError("Sample interval time must be positive")

        if end_ts <= start_ts:
            raise ValueError("End time must be greater than start time")

        self.sample_interval_ns = sample_interval_ns
        self.start_ts = start_ts
        self.end_ts = end_ts

        self.next_sample_ts = start_ts + sample_interval_ns

        self.flow = FlowAccumulator()

    def reset(self) -> None:
        self.next_sample_ts = self.start_ts + self.sample_interval_ns

        self.flow.reset()

    def observe_event(self, messages: list[db.MBOMsg], ts_event: int) -> None:
        """
        Adds one completed event to the flow bucket
        """
        if ts_event <= self.start_ts:
            return

        if ts_event > self.end_ts:
            return

        self.flow.observe_event(messages)

    def observe_bbo_ofi(self, ofi_increment: int) -> None:
        self.flow.observe_bbo_ofi(ofi_increment)

    def snapshot(self, ts_event: int, book: ReplayBook) -> FeatureRow | None:
        """
        Builds one feature observation
        """
        best_bid = book.best_bid()
        best_ask = book.best_ask()

        bid_depth_1, ask_depth_1 = depth(book, 1)
        bid_depth_5, ask_depth_5 = depth(book, 5)
        bid_depth_10, ask_depth_10 = depth(book, 10)

        raw_flow = self.flow.values()

        derived_flow: dict[str, int | float] = {
            "add_imbalance": add_imbalance(
                raw_flow["bid_add_volume"],
                raw_flow["ask_add_volume"]
            ),

            "cancel_imbalance": cancel_imbalance(
                raw_flow["bid_cancel_volume"],
                raw_flow["ask_cancel_volume"]
            ),

            "trade_imbalance": trade_imbalance(
                raw_flow["buy_trade_volume"],
                raw_flow["sell_trade_volume"]
            ),

            "book_pressure": book_pressure(
                raw_flow["bid_add_volume"],
                raw_flow["ask_add_volume"],
                raw_flow["bid_cancel_volume"],
                raw_flow["ask_cancel_volume"]
            ),

            "normalized_book_pressure": book_pressure_normalized(
                raw_flow["bid_add_volume"],
                raw_flow["ask_add_volume"],
                raw_flow["bid_cancel_volume"],
                raw_flow["ask_cancel_volume"]
            ),

            "total_add_volume": total_add_volume(
                raw_flow["bid_add_volume"],
                raw_flow["ask_add_volume"]
            ),

            "total_cancel_volume": total_cancel_volume(
                raw_flow["bid_cancel_volume"],
                raw_flow["ask_cancel_volume"]
            ),

            "total_trade_volume": total_trade_volume(
                raw_flow["buy_trade_volume"],
                raw_flow["sell_trade_volume"]
            ),

            "total_event_count": total_event_count(
                raw_flow["bid_add_count"],
                raw_flow["ask_add_count"],
                raw_flow["bid_cancel_count"],
                raw_flow["ask_cancel_count"],
                raw_flow["buy_fill_count"],
                raw_flow["sell_fill_count"]
            )
        }

        return {
            "ts_event": ts_event,

            "best_bid": None if best_bid is None else best_bid.price,
            "best_ask": None if best_ask is None else best_ask.price,

            "mid": mid_price(book),
            "spread": spread(book),
            "microprice": microprice(book),

            "bid_depth_1": bid_depth_1,
            "ask_depth_1": ask_depth_1,

            "bid_depth_5": bid_depth_5,
            "ask_depth_5": ask_depth_5,

            "bid_depth_10": bid_depth_10,
            "ask_depth_10": ask_depth_10,

            "imbalance_1": imbalance(book, 1),
            "imbalance_5": imbalance(book, 5),
            "imbalance_10": imbalance(book, 10),

            **raw_flow,
            **derived_flow
        }

    def emit_before(self, ts_event: int, book: ReplayBook) -> list[FeatureRow]:
        """
        Emits every scheduled observation before ts_event
        """
        rows: list[FeatureRow] = []

        while self.next_sample_ts < ts_event and self.next_sample_ts < self.end_ts:
            rows.append(
                self.snapshot(
                    ts_event=self.next_sample_ts,
                    book=book
                )
            )

            self.flow.reset()

            self.next_sample_ts += self.sample_interval_ns

        return rows

    def finish(self, book: ReplayBook) -> list[FeatureRow]:
        """
        Emits remaining observations through end of sampling window
        """
        rows: list[FeatureRow] = []

        while self.next_sample_ts <= self.end_ts:
            rows.append(
                self.snapshot(
                    ts_event=self.next_sample_ts,
                    book=book
                )
            )

            self.flow.reset()

            self.next_sample_ts += self.sample_interval_ns
    
        return rows
