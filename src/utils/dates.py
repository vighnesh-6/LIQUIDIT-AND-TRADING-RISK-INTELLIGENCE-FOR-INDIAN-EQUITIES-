"""Trading calendar and date utility functions.

Provides helper methods for handling Indian equity trading sessions and date calculations.
"""

from typing import List, Optional
import pandas as pd


def is_trading_day(date: str | pd.Timestamp) -> bool:
    """Checks whether a given date is a weekday (Monday-Friday).

    Note: NSE holiday calendar filtering can be extended during Phase 4.

    Args:
        date: Date string or timestamp.

    Returns:
        bool: True if weekday, False otherwise.
    """
    ts = pd.to_datetime(date)
    return ts.dayofweek < 5


def get_trading_days(
    start_date: str,
    end_date: Optional[str] = None,
) -> pd.DatetimeIndex:
    """Returns a DatetimeIndex of trading days between start and end date.

    Args:
        start_date: Start date string.
        end_date: Optional end date string; defaults to current date.

    Returns:
        pd.DatetimeIndex: Business days index.
    """
    end = pd.to_datetime(end_date) if end_date else pd.Timestamp.now()
    return pd.bdate_range(start=start_date, end=end)
