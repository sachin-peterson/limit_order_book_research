from src.features.utils import safe_divide

"""
pressure_normalized
bbo_ofi
"""

def add_imbalance(bid_add_volume: int, ask_add_volume: int) -> float:
    return safe_divide(
        bid_add_volume - ask_add_volume,
        bid_add_volume + ask_add_volume
    )


def cancel_imbalance(bid_cancel_volume: int, ask_cancel_volume: int) -> float:
    return safe_divide(
        bid_cancel_volume - ask_cancel_volume,
        bid_cancel_volume + ask_cancel_volume
    )


def trade_imbalance(buy_trade_volume: int, sell_trade_volume: int) -> float:
    return safe_divide(
        buy_trade_volume - sell_trade_volume,
        buy_trade_volume + sell_trade_volume
    )


def book_pressure(bid_add_vol: int, ask_add_vol: int, bid_cancel_vol: int, ask_cancel_vol: int) -> int:
    return (bid_add_vol + ask_cancel_vol) - (bid_cancel_vol + ask_add_vol)


def book_pressure_normalized(bid_add_vol: int, ask_add_vol: int, bid_cancel_vol: int, ask_cancel_vol: int) -> int:
    numerator = book_pressure(
        bid_add_vol, ask_add_vol, bid_cancel_vol, ask_cancel_vol
    )
    denominator = (
        bid_add_vol + ask_add_vol + bid_cancel_vol + ask_cancel_vol
    )

    return safe_divide(numerator, denominator)


def total_add_volume(bid_add_volume: int, ask_add_volume: int) -> int:
    return bid_add_volume + ask_add_volume


def total_cancel_volume(bid_cancel_volume: int, ask_cancel_volume: int) -> int:
    return bid_cancel_volume + ask_cancel_volume


def total_trade_volume(buy_trade_volume: int, sell_trade_volume: int) -> int:
    return buy_trade_volume + sell_trade_volume


def total_event_count(
        bid_add_count: int, 
        ask_add_count: int,
        bid_cancel_count: int, 
        ask_cancel_count: int, 
        buy_fill_count: int, 
        sell_fill_count: int
) -> int:
    return (
        bid_add_count
        + ask_add_count
        + bid_cancel_count
        + ask_cancel_count
        + buy_fill_count
        + sell_fill_count
    )

def bbo_ofi_increment(
    prev_bid_price: int,
    prev_bid_size: int,
    prev_ask_price: int,
    prev_ask_size: int,
    curr_bid_price: int,
    curr_bid_size: int,
    curr_ask_price: int,
    curr_ask_size: int
) -> int:
    if curr_bid_price > prev_bid_price:
        bid_contribution = curr_bid_size
    elif curr_bid_price == prev_bid_price:
        bid_contribution = curr_bid_size - prev_bid_size
    else:
        bid_contribution = -prev_bid_size

    if curr_ask_price < prev_ask_price:
        ask_contribution = -curr_ask_size
    elif curr_ask_price == prev_ask_price:
        ask_contribution = prev_ask_size - curr_ask_size
    else:
        ask_contribution = prev_ask_size

    return bid_contribution + ask_contribution