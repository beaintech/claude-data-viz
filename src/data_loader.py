import io, requests
import pandas as pd
from typing import Tuple

def load_from_upload(uploaded) -> Tuple[pd.DataFrame, str]:
    name = uploaded.name
    if name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded)
    elif name.lower().endswith(".xlsx"):
        df = pd.read_excel(uploaded)
    else:
        raise ValueError("Unsupported file type. Use .csv or .xlsx")
    return df, name

def load_from_gsheet_url(url: str) -> Tuple[pd.DataFrame, str]:
    # Expecting a CSV export URL
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    content = r.content
    df = pd.read_csv(io.BytesIO(content))
    return df, "GoogleSheets.csv"

def brief_summary(df: pd.DataFrame) -> str:
    parts = []
    parts.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    parts.append("Columns: " + ", ".join(map(str, df.columns[:20])) + ("..." if len(df.columns) > 20 else ""))
    nulls = df.isna().mean().round(3).to_dict()
    top_nulls = sorted(nulls.items(), key=lambda x: x[1], reverse=True)[:5]
    parts.append("Top missing-value columns: " + ", ".join(f"{k}: {v:.0%}" for k,v in top_nulls))
    return "\n".join(parts)