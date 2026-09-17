import pandas as pd


TARGET_500MS = 5
TARGET_1S = 10
TARGET_2S = 20
TARGET_5S = 50
TARGET_10S = 100


def add_return_targets(df: pd.DataFrame) -> pd.DataFrame:
    # Future mid-price movement (percentage return)
    df["target_return_500ms"] = df["mid"].shift(-TARGET_500MS) / df["mid"] - 1
    df["target_return_1s"] = df["mid"].shift(-TARGET_1S) / df["mid"] - 1
    df["target_return_2s"] = df["mid"].shift(-TARGET_2S) / df["mid"] - 1
    df["target_return_5s"] = df["mid"].shift(-TARGET_5S) / df["mid"] - 1
    df["target_return_10s"] = df["mid"].shift(-TARGET_10S) / df["mid"] - 1

    return df


def add_spread_move_targets(df: pd.DataFrame) -> pd.DataFrame:
    # Future mid-price movement normalized to current spread
    df["target_spread_move_500ms"] = (df["mid"].shift(-TARGET_500MS) - df["mid"]) / df["spread"]
    df["target_spread_move_1s"] = (df["mid"].shift(-TARGET_1S) - df["mid"]) / df["spread"]
    df["target_spread_move_2s"] = (df["mid"].shift(-TARGET_2S) - df["mid"]) / df["spread"]
    df["target_spread_move_5s"] = (df["mid"].shift(-TARGET_5S) - df["mid"]) / df["spread"]
    df["target_spread_move_10s"] = (df["mid"].shift(-TARGET_10S) - df["mid"]) / df["spread"]

    return df


def add_targets(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df = add_return_targets(df)
    df = add_spread_move_targets(df)

    return df
