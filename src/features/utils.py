def ns_from_ms(ms: int | float) -> int:
    return int(ms * 1_000_000)

def ns_from_s(seconds: int | float) -> int:
    return int(seconds * 1_000_000_000)

def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0

    return numerator / denominator