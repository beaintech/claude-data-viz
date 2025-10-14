import pandas as pd

def detect_time_column(df: pd.DataFrame):
    for col in df.columns:
        s = df[col]
        # If it's already datetime → accept
        if pd.api.types.is_datetime64_any_dtype(s):
            return col

        # ❌ Do NOT try to parse numeric columns as dates
        if pd.api.types.is_numeric_dtype(s):
            continue

        # Try parsing only object/string columns
        try:
            parsed = pd.to_datetime(s, errors='coerce', infer_datetime_format=True)
            ok_ratio = parsed.notna().mean()
            # require enough valid dates and sensible years
            if ok_ratio > 0.8:
                years = parsed.dt.year.dropna()
                if (years.between(1900, 2100).mean() > 0.95) and (years.nunique() >= 3):
                    df[col] = parsed
                    return col
        except Exception:
            pass
    return None
