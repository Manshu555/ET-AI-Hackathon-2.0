"""
Seed data for commissioning test templates.
Based on TIA-942, BICSI, and Uptime Tier standards.
"""
import json

TIA_942_POWER_TEMPLATE = {
    "name": "TIA-942 Power Distribution Test",
    "standard": "TIA-942",
    "system_type": "power",
    "steps": json.dumps([
        {"step_number": 1, "description": "Verify UPS input voltage (V)", "expected_min": 380, "expected_max": 420, "expected_unit": "V"},
        {"step_number": 2, "description": "Verify UPS output voltage (V)", "expected_min": 395, "expected_max": 405, "expected_unit": "V"},
        {"step_number": 3, "description": "Verify UPS output frequency (Hz)", "expected_min": 49.5, "expected_max": 50.5, "expected_unit": "Hz"},
        {"step_number": 4, "description": "Verify transfer switch operation time (ms)", "expected_min": 0, "expected_max": 10, "expected_unit": "ms"},
        {"step_number": 5, "description": "Verify generator start time (s)", "expected_min": 0, "expected_max": 15, "expected_unit": "s"},
        {"step_number": 6, "description": "Verify PDU output voltage per phase (V)", "expected_min": 220, "expected_max": 240, "expected_unit": "V"},
        {"step_number": 7, "description": "Battery autonomy test duration (min)", "expected_min": 10, "expected_max": 999, "expected_unit": "min"},
        {"step_number": 8, "description": "Verify earth fault loop impedance (Ω)", "expected_min": 0, "expected_max": 0.8, "expected_unit": "Ω"},
    ])
}

BICSI_COOLING_TEMPLATE = {
    "name": "BICSI Cooling System Commissioning",
    "standard": "BICSI",
    "system_type": "cooling",
    "steps": json.dumps([
        {"step_number": 1, "description": "Chilled water supply temperature (°C)", "expected_min": 6, "expected_max": 12, "expected_unit": "°C"},
        {"step_number": 2, "description": "Chilled water return temperature (°C)", "expected_min": 12, "expected_max": 18, "expected_unit": "°C"},
        {"step_number": 3, "description": "CRAC unit airflow rate (CFM)", "expected_min": 3000, "expected_max": 6000, "expected_unit": "CFM"},
        {"step_number": 4, "description": "Cold aisle temperature at rack inlet (°C)", "expected_min": 18, "expected_max": 27, "expected_unit": "°C"},
        {"step_number": 5, "description": "Hot aisle temperature at rack exhaust (°C)", "expected_min": 27, "expected_max": 45, "expected_unit": "°C"},
        {"step_number": 6, "description": "Relative humidity in whitespace (%)", "expected_min": 20, "expected_max": 80, "expected_unit": "%"},
        {"step_number": 7, "description": "Differential pressure across raised floor (Pa)", "expected_min": 10, "expected_max": 30, "expected_unit": "Pa"},
    ])
}

UPTIME_TIER_IT_TEMPLATE = {
    "name": "Uptime Tier III IT Infrastructure Test",
    "standard": "Uptime",
    "system_type": "IT",
    "steps": json.dumps([
        {"step_number": 1, "description": "Network switch port link speed (Gbps)", "expected_min": 10, "expected_max": 100, "expected_unit": "Gbps"},
        {"step_number": 2, "description": "UPS N+1 redundancy verification — modules online", "expected_min": 2, "expected_max": 10, "expected_unit": "count"},
        {"step_number": 3, "description": "Cross-connect fiber attenuation (dB)", "expected_min": 0, "expected_max": 3, "expected_unit": "dB"},
        {"step_number": 4, "description": "PDU load balancing deviation per phase (%)", "expected_min": 0, "expected_max": 10, "expected_unit": "%"},
        {"step_number": 5, "description": "Fire suppression system activation time (s)", "expected_min": 0, "expected_max": 60, "expected_unit": "s"},
        {"step_number": 6, "description": "Environmental monitoring sensor accuracy (±°C)", "expected_min": 0, "expected_max": 1, "expected_unit": "°C"},
    ])
}

ALL_TEMPLATES = [TIA_942_POWER_TEMPLATE, BICSI_COOLING_TEMPLATE, UPTIME_TIER_IT_TEMPLATE]
