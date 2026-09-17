from collections import OrderedDict
from dataclasses import dataclass, field

from .order import Order


@dataclass(slots=True)
class PriceLevel:
    price: int
    orders: OrderedDict[int, Order] = field(default_factory=OrderedDict)
    total_size: int = 0

    @property
    def order_count(self) -> int:
        return len(self.orders)

    def add(self, order: Order) -> None:
        self.orders[order.order_id] = order
        self.total_size += order.size

    def cancel(self, order_id: int, size: int) -> bool:
        order = self.orders[order_id]

        if size > order.size:
            raise ValueError("Cancel exceeds remaining order size")

        order.size -= size
        self.total_size -= size

        if order.size == 0:
            del self.orders[order_id]
            return True

        return False
