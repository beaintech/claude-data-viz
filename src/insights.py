import os
from typing import List, Optional
import pandas as pd
from .chart_suggester import ChartSpec

def _basic_stats(df: pd.DataFrame, chosen: List[ChartSpec]) -> str:
    lines = ["Insights (basic):"]
    for spec in chosen:
        if spec.kind in ("line", "bar") and spec.y:
            s = df[spec.y].dropna()
            if not s.empty:
                lines.append(f"- {spec.y}: min={s.min():.3g}, max={s.max():.3g}, mean={s.mean():.3g}")
    return "\n".join(lines)

def generate_insights(df: pd.DataFrame, chosen: List[ChartSpec], language: Optional[str] = None) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not language:
        return _basic_stats(df, chosen)

    # optional: call OpenAI for nicer prose
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        # Build a compact schema message
        points = []
        for spec in chosen:
            item = {"kind": spec.kind, "y": spec.y, "x": spec.x, "category": spec.category}
            points.append(item)

        prompt = (
            f"You are a data analyst. Write a short bullet list of insights in {language}. "
            "Be precise with numbers and trends. No fluff. "
            f"Charts context: {points[:5]} (at most 5). "
            "If time-series present, mention peaks and trends."
        )
        sample = df.head(200).to_dict(orient="list")  # small sample
        messages = [
            {"role": "system", "content": "Concise analytical writing. No emojis."},
            {"role": "user", "content": prompt + "\nData sample: " + str(sample)}
        ]
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return _basic_stats(df, chosen) + f"\n(Note: AI generation failed: {e})"