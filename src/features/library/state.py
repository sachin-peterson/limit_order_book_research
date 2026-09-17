from src.features.utils import safe_divide
from src.book.replay_book import ReplayBook


def mid_price(book: ReplayBook) -> float | None:
    bid = book.best_bid()
    ask = book.best_ask()

    if bid is None or ask is None:
        return None

    return (bid.price + ask.price) / 2


def spread(book: ReplayBook) -> int | None:
    bid = book.best_bid()
    ask = book.best_ask()

    if bid is None or ask is None:
        return None

    return ask.price - bid.price


def depth(book: ReplayBook, levels: int) -> tuple[int, int]:
    bids, asks = book.top_levels(levels)

    bid_depth = sum(level.total_size for level in bids)
    ask_depth = sum(level.total_size for level in asks)

    return bid_depth, ask_depth


def imbalance(book: ReplayBook, levels: int) -> float:
    bid_depth, ask_depth = depth(book, levels)

    return safe_divide(
        bid_depth - ask_depth, 
        bid_depth + ask_depth
    )


def microprice(book: ReplayBook) -> float | None:
    bid = book.best_bid()
    ask = book.best_ask()

    if bid is None or ask is None:
        return None

    bid_size = bid.total_size
    ask_size = ask.total_size
    total_size = bid_size + ask_size

    if total_size == 0:
        return None

    return (ask.price * bid_size + bid.price * ask_size) / total_size
