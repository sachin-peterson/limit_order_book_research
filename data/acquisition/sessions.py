from dataclasses import dataclass
from datetime import date

import pandas as pd
import pandas_market_calendars as mcal


@dataclass(slots=True)
class TradingSession:
    date: date
    request_start: pd.Timestamp
    market_open: pd.Timestamp
    market_close: pd.Timestamp


def get_trading_sessions(start_date: str, end_date: str) -> list[TradingSession]:
    calendar = mcal.get_calendar("NYSE")

    schedule = calendar.schedule(
        start_date=start_date,
        end_date=end_date
    )

    sessions = []

    for session_date, row in schedule.iterrows():
        session_day = session_date.date()

        request_start = pd.Timestamp(
            session_day,
            tz="UTC"
        )

        market_open = row["market_open"].tz_convert("UTC")
        market_close = row["market_close"].tz_convert("UTC")

        sessions.append(
            TradingSession(
                date=session_day,
                request_start=request_start,
                market_open=market_open,
                market_close=market_close
            )
        )

    return sessions
