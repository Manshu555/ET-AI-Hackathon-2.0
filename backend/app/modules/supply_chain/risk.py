"""
Supply chain risk scoring engine.
Combines: buffer days remaining, missed intermediate milestones, route risk weight.
"""
from datetime import date
from typing import List, Optional


# Static route risk weights — configurable per lane
ROUTE_RISK_WEIGHTS = {
    "default": 0.1,
    "international_sea": 0.3,
    "international_air": 0.15,
    "domestic": 0.05,
}


def compute_shipment_risk(
    required_on_site: Optional[date],
    missed_milestones: int = 0,
    total_milestones: int = 1,
    route_type: str = "default",
    status: str = "in_transit",
) -> float:
    """
    Compute a risk score (0-100) for a shipment.
    
    Components:
    - Buffer score (50%): how many days of buffer remain vs required-on-site
    - Milestone score (30%): ratio of missed intermediate milestones
    - Route weight (20%): static per-lane congestion/customs risk
    """
    if status == "delivered":
        return 0.0

    # Buffer score (0-1, higher = more risk)
    buffer_score = 0.5
    if required_on_site:
        days_remaining = (required_on_site - date.today()).days
        if days_remaining <= 0:
            buffer_score = 1.0
        elif days_remaining <= 7:
            buffer_score = 0.9
        elif days_remaining <= 14:
            buffer_score = 0.7
        elif days_remaining <= 30:
            buffer_score = 0.4
        else:
            buffer_score = max(0.1, 1.0 - (days_remaining / 90.0))

    # Milestone score
    milestone_score = 0.0
    if total_milestones > 0:
        milestone_score = min(missed_milestones / max(total_milestones, 1), 1.0)

    # Route weight
    route_weight = ROUTE_RISK_WEIGHTS.get(route_type, ROUTE_RISK_WEIGHTS["default"])

    # Weighted combination
    risk = (buffer_score * 0.50) + (milestone_score * 0.30) + (route_weight * 0.20)
    return round(min(risk * 100, 100), 1)


def get_risk_status(risk_score: float) -> str:
    """Map risk score to status label."""
    if risk_score >= 70:
        return "at_risk"
    elif risk_score >= 40:
        return "watch"
    else:
        return "on_track"


def suggest_mitigations(equipment_type: str, risk_score: float, days_remaining: Optional[int]) -> List[str]:
    """Generate mitigation suggestions for at-risk shipments."""
    suggestions = []

    if risk_score >= 70:
        suggestions.append(f"Consider expedited freight for {equipment_type}")
        suggestions.append("Contact vendor for updated ETA and acceleration options")
    
    if days_remaining is not None and days_remaining <= 7:
        suggestions.append("Alert project manager — delivery at critical risk of missing required-on-site date")
        suggestions.append("Check alternate vendor availability for same equipment category")

    if risk_score >= 40:
        suggestions.append("Increase tracking frequency to daily updates")

    if not suggestions:
        suggestions.append("Shipment on track — continue monitoring")

    return suggestions
