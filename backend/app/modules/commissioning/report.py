"""
PDF report generation for commissioning runs.
Generates a structured test record with pass/fail summary.
"""
import io
import json
from datetime import datetime


def generate_commissioning_report(run_detail: dict) -> bytes:
    """
    Generate a text-based commissioning report.
    In production, this would use a docx/PDF pipeline.
    For the hackathon, we generate a structured text report.
    """
    lines = []
    lines.append("=" * 70)
    lines.append("          COMMISSIONING TEST REPORT")
    lines.append("          EPC-Intel Platform")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Report Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"Test Template:    {run_detail.get('template_name', 'N/A')}")
    lines.append(f"Standard:         {run_detail.get('standard', 'N/A')}")
    lines.append(f"Project ID:       {run_detail.get('project_id', 'N/A')}")
    lines.append(f"Run ID:           {run_detail.get('id', 'N/A')}")
    lines.append(f"Engineer ID:      {run_detail.get('engineer_id', 'N/A')}")
    lines.append(f"Status:           {run_detail.get('status', 'N/A').upper()}")
    lines.append(f"Started:          {run_detail.get('started_at', 'N/A')}")
    lines.append(f"Completed:        {run_detail.get('completed_at', 'N/A')}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("SUMMARY")
    lines.append("-" * 70)
    lines.append(f"  Total Steps:   {run_detail.get('pass_count', 0) + run_detail.get('fail_count', 0) + run_detail.get('pending_count', 0)}")
    lines.append(f"  Passed:        {run_detail.get('pass_count', 0)}")
    lines.append(f"  Failed:        {run_detail.get('fail_count', 0)}")
    lines.append(f"  Pending:       {run_detail.get('pending_count', 0)}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("DETAILED TEST RESULTS")
    lines.append("-" * 70)

    for step in run_detail.get("steps", []):
        status_marker = "✓ PASS" if step["status"] == "pass" else ("✗ FAIL" if step["status"] == "fail" else "○ PENDING")
        lines.append(f"\n  Step {step['step_number']}: {step['description']}")
        expected = f"    Expected: {step.get('expected_min', '?')} – {step.get('expected_max', '?')} {step.get('expected_unit', '')}"
        lines.append(expected)
        if step.get("actual_value") is not None:
            lines.append(f"    Actual:   {step['actual_value']} {step.get('expected_unit', '')}")
        lines.append(f"    Result:   {status_marker}")
        if step.get("deviation_id"):
            lines.append(f"    ⚠ Deviation Created: {step['deviation_id']}")

    lines.append("")
    lines.append("-" * 70)
    lines.append("SIGNATURES")
    lines.append("-" * 70)
    lines.append("")
    lines.append("  Test Engineer: _______________________  Date: ____________")
    lines.append("")
    lines.append("  QA Manager:    _______________________  Date: ____________")
    lines.append("")
    lines.append("  Project Manager: ____________________  Date: ____________")
    lines.append("")
    lines.append("=" * 70)
    lines.append("         END OF COMMISSIONING REPORT")
    lines.append("=" * 70)

    return "\n".join(lines).encode("utf-8")
