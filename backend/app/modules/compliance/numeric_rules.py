import re

def extract_numeric_value(text: str) -> float | None:
    """A deterministic rule engine for extracting numeric values from text."""
    match = re.search(r'\b(\d+(\.\d+)?)\b', text)
    if match:
        return float(match.group(1))
    return None
