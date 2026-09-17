from sortedcontainers import SortedDict

from .order import Order
from .price_level import PriceLevel


class ReplayBook:
    def __init__(self):
        self.bids: SortedDict[int, PriceLevel] = SortedDict()
        self.asks: SortedDict[int, PriceLevel] = SortedDict()
        self.order_index: dict[int, Order] = {}

    def reset(self) -> None:
        self.bids.clear()
        self.asks.clear()
        self.order_index.clear()

    def side(self, side: str) -> SortedDict:
        if side == "B":
            return self.bids
        if side == "A":
            return self.asks
        raise ValueError(f"Invalid side: {side}")

    def add(self, order_id: int, side: str, price: int, size: int, ts_event: int) -> None:
        if order_id in self.order_index:
            raise ValueError(f"Duplicate order ID: {order_id}")

        order = Order(order_id, side, price, size, ts_event)
        levels = self.side(side)

        if price not in levels:
            levels[price] = PriceLevel(price)

        levels[price].add(order)
        self.order_index[order_id] = order

    def cancel(self, order_id: int, size: int) -> None:
        order = self.order_index[order_id]
        levels = self.side(order.side)
        level = levels[order.price]

        removed = level.cancel(order_id, size)

        if removed:
            del self.order_index[order_id]

        if level.order_count == 0:
            del levels[order.price]

    def best_bid(self):
        return None if not self.bids else self.bids.peekitem(-1)[1]

    def best_ask(self):
        return None if not self.asks else self.asks.peekitem(0)[1]


    def top_levels(self, depth=10):
        bids = [
            self.bids.peekitem(i)[1]
            for i in range(len(self.bids) - 1, max(-1, len(self.bids) - depth - 1), -1)
        ]

        asks = [
            self.asks.peekitem(i)[1]
            for i in range(min(depth, len(self.asks)))
        ]

        return bids, asks
