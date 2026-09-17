from dataclasses import dataclass


@dataclass(slots=True)
class Order:
    order_id: int
    side: str
    price: int
    size: int
    ts_event: int
