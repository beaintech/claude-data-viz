from typing import List, Optional
import pandas as pd
from pydantic import BaseModel
from .utils import detect_time_column

class ChartSpec(BaseModel):
    kind: str                 # line | bar | pie
    x: Optional[str] = None
    y: Optional[str] = None
    category: Optional[str] = None
    agg: str = "sum"
    title: Optional[str] = None

def suggest_charts(df: pd.DataFrame) -> List[ChartSpec]:
    specs: List[ChartSpec] = []
    # try time-series line
    time_col = detect_time_column(df)
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if df[c].dtype == 'object' or pd.api.types.is_categorical_dtype(df[c])]

    if time_col and numeric_cols:
        y = numeric_cols[0]
        specs.append(ChartSpec(kind="line", x=time_col, y=y, title=f"{y} over time"))

    # bar for category vs numeric
    if cat_cols and numeric_cols:
        specs.append(ChartSpec(kind="bar", x=cat_cols[0], y=numeric_cols[0], title=f"{numeric_cols[0]} by {cat_cols[0]}"))

    # pie for category share
    if cat_cols and numeric_cols:
        specs.append(ChartSpec(kind="pie", category=cat_cols[0], y=numeric_cols[0], title=f"Share of {numeric_cols[0]} by {cat_cols[0]}"))

    # fallback: bar of first two numeric columns
    if not specs and len(numeric_cols) >= 2:
        specs.append(ChartSpec(kind="bar", x=numeric_cols[0], y=numeric_cols[1], title=f"{numeric_cols[1]} by {numeric_cols[0]}"))

    # ensure at least one
    if not specs and numeric_cols:
        specs.append(ChartSpec(kind="bar", x=df.columns[0], y=numeric_cols[0], title=f"{numeric_cols[0]} by {df.columns[0]}"))
    return specs