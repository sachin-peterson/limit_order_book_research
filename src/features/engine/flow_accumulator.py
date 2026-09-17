from dataclasses import dataclass

import databento as db


FlowValues = dict[str, int]


@dataclass(slots=True)
class FlowAccumulator:
    bid_add_volume: int = 0
    ask_add_volume: int = 0

    bid_add_count: int = 0
    ask_add_count: int = 0

    bid_cancel_volume: int = 0
    ask_cancel_volume: int = 0

    bid_cancel_count: int = 0
    ask_cancel_count: int = 0

    buy_trade_volume: int = 0
    sell_trade_volume: int = 0

    buy_fill_count: int = 0
    sell_fill_count: int = 0

    bbo_ofi: int = 0

    def reset(self) -> None:
        self.bid_add_volume = 0
        self.ask_add_volume = 0

        self.bid_add_count = 0
        self.ask_add_count = 0

        self.bid_cancel_volume = 0
        self.ask_cancel_volume = 0

        self.bid_cancel_count = 0
        self.ask_cancel_count = 0

        self.buy_trade_volume = 0
        self.sell_trade_volume = 0

        self.buy_fill_count = 0
        self.sell_fill_count = 0

        self.bbo_ofi = 0

    def observe_event(self, messages: list[db.MBOMsg]) -> None:
        """
        Accumulates flow from one copmleted event
        """
        fill_by_order: dict[int, int] = {}

        # Identify executions
        for msg in messages:
            if msg.action != "F":
                continue

            fill_by_order[msg.order_id] = fill_by_order.get(msg.order_id, 0) + msg.size

            if msg.side == "A":
                self.buy_trade_volume += msg.size
                self.buy_fill_count += 1

            elif msg.side == "B":
                self.sell_trade_volume += msg.size
                self.sell_fill_count += 1

        # Process adds and genuine cancellations
        for msg in messages:
            if msg.action == "A":
                self.observe_add(msg)

            elif msg.action == "C":
                filled_size = fill_by_order.get(msg.order_id, 0)
                matched_fill = min(msg.size, filled_size)
                cancel_size = msg.size - matched_fill

                if matched_fill > 0:
                    fill_by_order[msg.order_id] -= matched_fill

                if cancel_size > 0:
                    self.observe_cancel(msg, cancel_size)

    def observe_add(self, msg: db.MBOMsg) -> None:
        if msg.side == "B":
            self.bid_add_volume += msg.size
            self.bid_add_count += 1

        elif msg.side == "A":
            self.ask_add_volume += msg.size
            self.ask_add_count += 1

    def observe_cancel(self, msg: db.MBOMsg, size: int | None = None) -> None:
        cancel_size = msg.size if size is None else size

        if msg.side == "B":
            self.bid_cancel_volume += cancel_size
            self.bid_cancel_count += 1

        elif msg.side == "A":
            self.ask_cancel_volume += cancel_size
            self.ask_cancel_count += 1

    def observe_bbo_ofi(self, ofi_increment: int) -> None:
        self.bbo_ofi += ofi_increment

    def values(self) -> FlowValues:
        return {
            "bid_add_volume": self.bid_add_volume,
            "ask_add_volume": self.ask_add_volume,

            "bid_cancel_volume": self.bid_cancel_volume,
            "ask_cancel_volume": self.ask_cancel_volume,

            "buy_trade_volume": self.buy_trade_volume,
            "sell_trade_volume": self.sell_trade_volume,

            "bid_add_count": self.bid_add_count,
            "ask_add_count": self.ask_add_count,

            "bid_cancel_count": self.bid_cancel_count,
            "ask_cancel_count": self.ask_cancel_count,

            "buy_fill_count": self.buy_fill_count,
            "sell_fill_count": self.sell_fill_count,

            "bbo_ofi": self.bbo_ofi
        }