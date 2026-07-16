"""
Feature engineering for the Schedule Risk model.
Computes six features per task as described in Section 10.3:
1. Lead-time variance vs plan
2. Upstream dependency slippage
3. Workforce fill rate
4. Weather severity index (stubbed for hackathon)
5. Vendor on-time-delivery history (stubbed)
6. Task completion ratio
"""
from datetime import date, timedelta
from typing import List, Optional
import json


def compute_lead_time_variance(planned_start: Optional[date], planned_end: Optional[date],
                                actual_start: Optional[date], actual_end: Optional[date]) -> float:
    """Positive = behind schedule, negative = ahead."""
    if planned_end and actual_end:
        return (actual_end - planned_end).days
    if planned_start and actual_start:
        return (actual_start - planned_start).days
    if planned_end:
        today = date.today()
        if today > planned_end:
            return (today - planned_end).days
    return 0.0


def compute_upstream_slippage(task_deps: Optional[str], all_tasks: dict) -> float:
    """Average delay days of upstream dependencies."""
    if not task_deps:
        return 0.0
    try:
        dep_ids = json.loads(task_deps)
    except (json.JSONDecodeError, TypeError):
        return 0.0

    slippages = []
    for dep_id in dep_ids:
        dep_task = all_tasks.get(dep_id)
        if dep_task and dep_task.get("planned_end"):
            actual = dep_task.get("actual_end") or date.today()
            planned = dep_task["planned_end"]
            slip = (actual - planned).days if isinstance(actual, date) and isinstance(planned, date) else 0
            slippages.append(max(slip, 0))

    return sum(slippages) / len(slippages) if slippages else 0.0


def compute_workforce_fill_rate(availability: Optional[float]) -> float:
    """Returns 1.0 - (availability / 100). Higher = more risk."""
    if availability is None:
        return 0.5  # default medium risk if unknown
    return max(0.0, 1.0 - (availability / 100.0))


def compute_weather_severity() -> float:
    """7-day weather severity index at project location.
    Returns zero until a versioned weather feed is integrated."""
    return 0.0


def compute_vendor_otd_history() -> float:
    """Vendor on-time delivery history.
    Returns zero until vendor performance data is integrated."""
    return 0.0


def compute_task_progress_ratio(planned_start: Optional[date], planned_end: Optional[date],
                                 actual_start: Optional[date], status: str) -> float:
    """How far behind the expected progress is the task. 0 = on track, 1 = very behind."""
    if status == "completed":
        return 0.0
    if not planned_start or not planned_end:
        return 0.5

    total_duration = (planned_end - planned_start).days or 1
    today = date.today()
    elapsed = (today - planned_start).days
    expected_pct = min(elapsed / total_duration, 1.0)

    if status == "not_started" and expected_pct > 0.1:
        return min(expected_pct, 1.0)
    if status == "in_progress" and actual_start:
        actual_elapsed = (today - actual_start).days
        return max(0.0, expected_pct - (actual_elapsed / total_duration))
    return 0.0


def compute_features(task: dict, all_tasks: dict) -> dict:
    """Compute all six features for a single task."""
    lead_time = compute_lead_time_variance(
        task.get("planned_start"), task.get("planned_end"),
        task.get("actual_start"), task.get("actual_end")
    )
    upstream = compute_upstream_slippage(task.get("dependencies"), all_tasks)
    workforce = compute_workforce_fill_rate(task.get("workforce_availability"))
    weather = compute_weather_severity()
    vendor = compute_vendor_otd_history()
    progress = compute_task_progress_ratio(
        task.get("planned_start"), task.get("planned_end"),
        task.get("actual_start"), task.get("status", "not_started")
    )

    return {
        "lead_time_variance": lead_time,
        "upstream_slippage": upstream,
        "workforce_gap": workforce,
        "weather_severity": weather,
        "vendor_otd_risk": vendor,
        "progress_deficit": progress,
    }


def compute_risk_score(features: dict) -> float:
    """Weighted sum risk score (0-100). Replaces LightGBM for hackathon."""
    weights = {
        "lead_time_variance": 0.30,
        "upstream_slippage": 0.25,
        "workforce_gap": 0.15,
        "weather_severity": 0.10,
        "vendor_otd_risk": 0.10,
        "progress_deficit": 0.10,
    }

    # Normalize lead_time and upstream to 0-1 range (cap at 30 days)
    normalized = {
        "lead_time_variance": min(max(features["lead_time_variance"], 0) / 30.0, 1.0),
        "upstream_slippage": min(features["upstream_slippage"] / 15.0, 1.0),
        "workforce_gap": features["workforce_gap"],
        "weather_severity": features["weather_severity"],
        "vendor_otd_risk": features["vendor_otd_risk"],
        "progress_deficit": features["progress_deficit"],
    }

    raw = sum(normalized[k] * weights[k] for k in weights)
    return round(min(raw * 100, 100), 1)


def get_contributing_factors(features: dict) -> List[dict]:
    """Return ranked contributing factors in plain language."""
    factor_labels = {
        "lead_time_variance": "Schedule behind plan",
        "upstream_slippage": "Upstream dependency delayed",
        "workforce_gap": "Workforce shortage",
        "weather_severity": "Adverse weather forecast",
        "vendor_otd_risk": "Vendor delivery risk",
        "progress_deficit": "Task progress behind expectation",
    }

    # Sort by normalized impact
    items = []
    for key, label in factor_labels.items():
        val = features.get(key, 0)
        if key == "lead_time_variance":
            impact = min(max(val, 0) / 30.0, 1.0)
        elif key == "upstream_slippage":
            impact = min(val / 15.0, 1.0)
        else:
            impact = val

        if impact > 0.05:
            items.append({"factor": label, "impact": round(impact, 2), "raw_value": round(val, 2)})

    items.sort(key=lambda x: x["impact"], reverse=True)
    return items[:5]
