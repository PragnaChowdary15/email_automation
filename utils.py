"""
utils.py
--------
Shared utility functions used across the project.
"""

import pandas as pd


def parse_dates(series):
    """
    Try common date formats in order — zero warnings.
    Supports: DD-MM-YYYY | YYYY-MM-DD | DD/MM/YYYY | MM/DD/YYYY
    """
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y",
                "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d"):
        try:
            return pd.to_datetime(series, format=fmt)
        except (ValueError, TypeError):
            continue

    raise ValueError(
        "Could not parse Exam_Date.\n"
        "Supported formats: DD-MM-YYYY  |  YYYY-MM-DD  |  DD/MM/YYYY"
    )
