import pandas as pd

THAI_MONTHS_SHORT = [
    "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
]

def to_thai_year(df, date_col='date'):
    """Transform date to Thai Year (B.E.). Format: 'yyyy'"""
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col])

    df['thai_year'] = df[date_col].dt.year + 543
    df['thai_year_label'] = df['thai_year'].astype(str)
    return df

def to_thai_quarter(df, date_col='date'):
    """Transform date to Thai Quarter format. Format: 'Qx-yyyy' (e.g., Q1-2567)"""
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col])

    df['thai_quarter'] = df[date_col].dt.quarter
    df['thai_year'] = df[date_col].dt.year + 543

    df['thai_quarter_label'] = "Q" + df['thai_quarter'].astype(str) + "-" + df['thai_year'].astype(str)
    return df

def to_thai_month(df, date_col='date'):
    """Transform date to Thai Monthly format. Format: 'ม.ค. yyyy'"""
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col])

    df['thai_month'] = df[date_col].dt.month.apply(lambda x: THAI_MONTHS_SHORT[x-1])
    df['thai_year'] = df[date_col].dt.year + 543

    df['thai_month_label'] = df['thai_month'] + " " + df['thai_year'].astype(str)
    return df
