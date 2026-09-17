import pandas as pd


WINDOW_500MS = 5
WINDOW_1S = 10
WINDOW_5S = 50


def add_momentum_features(df: pd.DataFrame) -> pd.DataFrame:
    # Mid-price percentage return
    df["mid_return_500ms"] = df["mid"] / df["mid"].shift(WINDOW_500MS) - 1
    df["mid_return_1s"] = df["mid"] / df["mid"].shift(WINDOW_1S) - 1
    df["mid_return_5s"] = df["mid"] / df["mid"].shift(WINDOW_5S) - 1

    # Microprice percentage return
    df["microprice_return_500ms"] = df["microprice"] / df["microprice"].shift(WINDOW_500MS) - 1
    df["microprice_return_1s"] = df["microprice"] / df["microprice"].shift(WINDOW_1S) - 1
    df["microprice_return_5s"] = df["microprice"] / df["microprice"].shift(WINDOW_5S) - 1

    # Microprice relative to mid
    df["microprice_skew"] = (df["microprice"] - df["mid"]) / df["spread"]

    return df


def add_flow_features(df: pd.DataFrame) -> pd.DataFrame:
    # BBO order flow imbalance
    df["bbo_ofi_500ms"] = df["bbo_ofi"].rolling(window=WINDOW_500MS, min_periods=WINDOW_500MS).sum()
    df["bbo_ofi_1s"] = df["bbo_ofi"].rolling(window=WINDOW_1S, min_periods=WINDOW_1S).sum()
    df["bbo_ofi_5s"] = df["bbo_ofi"].rolling(window=WINDOW_5S, min_periods=WINDOW_5S).sum()

    # Book pressure
    df["book_pressure_500ms"] = df["book_pressure"].rolling(window=WINDOW_500MS, min_periods=WINDOW_500MS).sum()
    df["book_pressure_1s"] = df["book_pressure"].rolling(window=WINDOW_1S, min_periods=WINDOW_1S).sum()
    df["book_pressure_5s"] = df["book_pressure"].rolling(window=WINDOW_5S, min_periods=WINDOW_5S).sum()

    # Trade imbalance
    buy_trade_volume_500ms = df["buy_trade_volume"].rolling(window=WINDOW_500MS, min_periods=WINDOW_500MS).sum()
    sell_trade_volume_500ms = df["sell_trade_volume"].rolling(window=WINDOW_500MS, min_periods=WINDOW_500MS).sum()
    trade_diff_500ms = buy_trade_volume_500ms - sell_trade_volume_500ms
    trade_total_500ms = buy_trade_volume_500ms + sell_trade_volume_500ms

    df["trade_imbalance_500ms"] = trade_diff_500ms / trade_total_500ms.where(trade_total_500ms != 0, 1)
    df.loc[trade_total_500ms == 0, "trade_imbalance_500ms"] = 0.0

    buy_trade_volume_1s = df["buy_trade_volume"].rolling(window=WINDOW_1S, min_periods=WINDOW_1S).sum()
    sell_trade_volume_1s = df["sell_trade_volume"].rolling(window=WINDOW_1S, min_periods=WINDOW_1S).sum()
    trade_diff_1s = buy_trade_volume_1s - sell_trade_volume_1s
    trade_total_1s = buy_trade_volume_1s + sell_trade_volume_1s

    df["trade_imbalance_1s"] = trade_diff_1s / trade_total_1s.where(trade_total_1s != 0, 1)
    df.loc[trade_total_1s == 0, "trade_imbalance_1s"] = 0.0

    buy_trade_volume_5s = df["buy_trade_volume"].rolling(window=WINDOW_5S, min_periods=WINDOW_5S).sum()
    sell_trade_volume_5s = df["sell_trade_volume"].rolling(window=WINDOW_5S, min_periods=WINDOW_5S).sum()
    trade_diff_5s = buy_trade_volume_5s - sell_trade_volume_5s
    trade_total_5s = buy_trade_volume_5s + sell_trade_volume_5s

    df["trade_imbalance_5s"] = trade_diff_5s / trade_total_5s.where(trade_total_5s != 0, 1)
    df.loc[trade_total_5s == 0, "trade_imbalance_5s"] = 0.0

    # Cancellation imbalance
    bid_cancel_volume_500ms = df["bid_cancel_volume"].rolling(window=WINDOW_500MS, min_periods=WINDOW_500MS).sum()
    ask_cancel_volume_500ms = df["ask_cancel_volume"].rolling(window=WINDOW_500MS, min_periods=WINDOW_500MS).sum()
    cancel_diff_500ms = ask_cancel_volume_500ms - bid_cancel_volume_500ms
    cancel_total_500ms = bid_cancel_volume_500ms + ask_cancel_volume_500ms

    df["cancel_imbalance_500ms"] = cancel_diff_500ms / cancel_total_500ms.where(cancel_total_500ms != 0, 1)
    df.loc[cancel_total_500ms == 0, "cancel_imbalance_500ms"] = 0.0

    bid_cancel_volume_1s = df["bid_cancel_volume"].rolling(window=WINDOW_1S, min_periods=WINDOW_1S).sum()
    ask_cancel_volume_1s = df["ask_cancel_volume"].rolling(window=WINDOW_1S, min_periods=WINDOW_1S).sum()
    cancel_diff_1s = ask_cancel_volume_1s - bid_cancel_volume_1s
    cancel_total_1s = bid_cancel_volume_1s + ask_cancel_volume_1s

    df["cancel_imbalance_1s"] = cancel_diff_1s / cancel_total_1s.where(cancel_total_1s != 0, 1)
    df.loc[cancel_total_1s == 0, "cancel_imbalance_1s"] = 0.0

    bid_cancel_volume_5s = df["bid_cancel_volume"].rolling(window=WINDOW_5S, min_periods=WINDOW_5S).sum()
    ask_cancel_volume_5s = df["ask_cancel_volume"].rolling(window=WINDOW_5S, min_periods=WINDOW_5S).sum()
    cancel_diff_5s = ask_cancel_volume_5s - bid_cancel_volume_5s
    cancel_total_5s = bid_cancel_volume_5s + ask_cancel_volume_5s

    df["cancel_imbalance_5s"] = cancel_diff_5s / cancel_total_5s.where(cancel_total_5s != 0, 1)
    df.loc[cancel_total_5s == 0, "cancel_imbalance_5s"] = 0.0

    # Add imbalance
    bid_add_volume_500ms = df["bid_add_volume"].rolling(WINDOW_500MS, min_periods=WINDOW_500MS).sum()
    ask_add_volume_500ms = df["ask_add_volume"].rolling(WINDOW_500MS, min_periods=WINDOW_500MS).sum()
    add_diff_500ms = bid_add_volume_500ms - ask_add_volume_500ms
    add_total_500ms = bid_add_volume_500ms + ask_add_volume_500ms

    df["add_imbalance_500ms"] = add_diff_500ms / add_total_500ms.where(add_total_500ms != 0, 1)
    df.loc[add_total_500ms == 0, "add_imbalance_500ms"] = 0.0

    bid_add_volume_1s = df["bid_add_volume"].rolling(WINDOW_1S, min_periods=WINDOW_1S).sum()
    ask_add_volume_1s = df["ask_add_volume"].rolling(WINDOW_1S, min_periods=WINDOW_1S).sum()
    add_diff_1s = bid_add_volume_1s - ask_add_volume_1s
    add_total_1s = bid_add_volume_1s + ask_add_volume_1s

    df["add_imbalance_1s"] = add_diff_1s / add_total_1s.where(add_total_1s != 0, 1)
    df.loc[add_total_1s == 0, "add_imbalance_1s"] = 0.0

    bid_add_volume_5s = df["bid_add_volume"].rolling(WINDOW_5S, min_periods=WINDOW_5S).sum()
    ask_add_volume_5s = df["ask_add_volume"].rolling(WINDOW_5S, min_periods=WINDOW_5S).sum()
    add_diff_5s = bid_add_volume_5s - ask_add_volume_5s
    add_total_5s = bid_add_volume_5s + ask_add_volume_5s

    df["add_imbalance_5s"] = add_diff_5s / add_total_5s.where(add_total_5s != 0, 1)
    df.loc[add_total_5s == 0, "add_imbalance_5s"] = 0.0

    # Normalized book pressure
    pressure_diff_500ms = bid_add_volume_500ms + ask_cancel_volume_500ms - ask_add_volume_500ms - bid_cancel_volume_500ms
    pressure_total_500ms = bid_add_volume_500ms + ask_add_volume_500ms + bid_cancel_volume_500ms + ask_cancel_volume_500ms
    df["normalized_book_pressure_500ms"] = pressure_diff_500ms / pressure_total_500ms.where(pressure_total_500ms != 0, 1)
    df.loc[pressure_total_500ms == 0, "normalized_book_pressure_500ms"] = 0.0

    pressure_diff_1s = bid_add_volume_1s + ask_cancel_volume_1s - ask_add_volume_1s - bid_cancel_volume_1s
    pressure_total_1s = bid_add_volume_1s + ask_add_volume_1s + bid_cancel_volume_1s + ask_cancel_volume_1s
    df["normalized_book_pressure_1s"] = pressure_diff_1s / pressure_total_1s.where(pressure_total_1s != 0, 1)
    df.loc[pressure_total_1s == 0, "normalized_book_pressure_1s"] = 0.0

    pressure_diff_5s = bid_add_volume_5s + ask_cancel_volume_5s - ask_add_volume_5s - bid_cancel_volume_5s
    pressure_total_5s = bid_add_volume_5s + ask_add_volume_5s + bid_cancel_volume_5s + ask_cancel_volume_5s
    df["normalized_book_pressure_5s"] = pressure_diff_5s / pressure_total_5s.where(pressure_total_5s != 0, 1)
    df.loc[pressure_total_5s == 0, "normalized_book_pressure_5s"] = 0.0

    return df


def add_imbalance_features(df: pd.DataFrame) -> pd.DataFrame:
    # Imbalance persistence
    df["imbalance_1_mean_500ms"] = df["imbalance_1"].rolling(WINDOW_500MS, min_periods=WINDOW_500MS).mean()
    df["imbalance_5_mean_500ms"] = df["imbalance_5"].rolling(WINDOW_500MS, min_periods=WINDOW_500MS).mean()
    df["imbalance_10_mean_500ms"] = df["imbalance_10"].rolling(WINDOW_500MS, min_periods=WINDOW_500MS).mean()

    df["imbalance_1_mean_1s"] = df["imbalance_1"].rolling(WINDOW_1S, min_periods=WINDOW_1S).mean()
    df["imbalance_5_mean_1s"] = df["imbalance_5"].rolling(WINDOW_1S, min_periods=WINDOW_1S).mean()
    df["imbalance_10_mean_1s"] = df["imbalance_10"].rolling(WINDOW_1S, min_periods=WINDOW_1S).mean()

    df["imbalance_1_mean_5s"] = df["imbalance_1"].rolling(WINDOW_5S, min_periods=WINDOW_5S).mean()
    df["imbalance_5_mean_5s"] = df["imbalance_5"].rolling(WINDOW_5S, min_periods=WINDOW_5S).mean()
    df["imbalance_10_mean_5s"] = df["imbalance_10"].rolling(WINDOW_5S, min_periods=WINDOW_5S).mean()

    return df


def add_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
    # Std. dev. volatility
    return_100ms = df["mid"] / df["mid"].shift(1) - 1

    df["volatility_500ms"] = return_100ms.rolling(WINDOW_500MS, min_periods=WINDOW_500MS).std()
    df["volatility_1s"] = return_100ms.rolling(WINDOW_1S, min_periods=WINDOW_1S).std()
    df["volatility_5s"] = return_100ms.rolling(WINDOW_5S, min_periods=WINDOW_5S).std()

    return df


def add_activity_features(df: pd.DataFrame) -> pd.DataFrame:
    # Event intensity
    df["event_count_500ms"] = df["total_event_count"].rolling(WINDOW_500MS, min_periods=WINDOW_500MS).sum()
    df["event_count_1s"] = df["total_event_count"].rolling(WINDOW_1S, min_periods=WINDOW_1S).sum()
    df["event_count_5s"] = df["total_event_count"].rolling(WINDOW_5S, min_periods=WINDOW_5S).sum()

    # Trade intensity
    trade_count = df["buy_fill_count"] + df["sell_fill_count"]
    df["trade_count_500ms"] = trade_count.rolling(WINDOW_500MS, min_periods=WINDOW_500MS).sum()
    df["trade_count_1s"] = trade_count.rolling(WINDOW_1S, min_periods=WINDOW_1S).sum()
    df["trade_count_5s"] = trade_count.rolling(WINDOW_5S, min_periods=WINDOW_5S).sum()

    # Cancel intensity
    cancel_count = df["bid_cancel_count"] + df["ask_cancel_count"]
    df["cancel_count_500ms"] = cancel_count.rolling(WINDOW_500MS, min_periods=WINDOW_500MS).sum()
    df["cancel_count_1s"] = cancel_count.rolling(WINDOW_1S, min_periods=WINDOW_1S).sum()
    df["cancel_count_5s"] = cancel_count.rolling(WINDOW_5S, min_periods=WINDOW_5S).sum()

    # Volume intensity
    df["add_volume_500ms"] = df["total_add_volume"].rolling(WINDOW_500MS, min_periods=WINDOW_500MS).sum()
    df["add_volume_1s"] = df["total_add_volume"].rolling(WINDOW_1S, min_periods=WINDOW_1S).sum()
    df["add_volume_5s"] = df["total_add_volume"].rolling(WINDOW_5S, min_periods=WINDOW_5S).sum()

    df["cancel_volume_500ms"] = df["total_cancel_volume"].rolling(WINDOW_500MS, min_periods=WINDOW_500MS).sum()
    df["cancel_volume_1s"] = df["total_cancel_volume"].rolling(WINDOW_1S, min_periods=WINDOW_1S).sum()
    df["cancel_volume_5s"] = df["total_cancel_volume"].rolling(WINDOW_5S, min_periods=WINDOW_5S).sum()

    df["trade_volume_500ms"] = df["total_trade_volume"].rolling(WINDOW_500MS, min_periods=WINDOW_500MS).sum()
    df["trade_volume_1s"] = df["total_trade_volume"].rolling(WINDOW_1S, min_periods=WINDOW_1S).sum()
    df["trade_volume_5s"] = df["total_trade_volume"].rolling(WINDOW_5S, min_periods=WINDOW_5S).sum()
    
    return df


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df = add_momentum_features(df)
    df = add_flow_features(df)
    df = add_imbalance_features(df)
    df = add_volatility_features(df)
    df = add_activity_features(df)

    return df
