"""Synthetic Karnataka context used only for deterministic development fixtures."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Station:
    ps_code: str
    district_code: str
    station_number: str
    name: str
    district: str
    zone: str


STATIONS = (
    Station("KA-BLR-C-042", "BLR-C", "042", "Whitefield Synthetic Police Station", "Bangalore City", "East Zone"),
    Station("KA-BLR-C-006", "BLR-C", "006", "KR Puram Synthetic Police Station", "Bangalore City", "East Zone"),
    Station("KA-BLR-C-051", "BLR-C", "051", "Jayanagar Synthetic Police Station", "Bangalore City", "South Zone"),
    Station("KA-MYS-015", "MYS", "015", "Devaraja Synthetic Police Station", "Mysore", "Mysore Zone"),
)

CRIME_CATEGORIES = (
    ("Vehicle Theft", (379,), "master key; parked two-wheeler; late night"),
    ("Cybercrime", (420,), "fake refund call; one-time password; UPI transfer"),
    ("Fraud/Cheating", (420, 406), "investment promise; bank transfer; repeated contact"),
    ("Chain Snatching", (356, 379), "two-wheeler approach; evening road; quick escape"),
)

IPC_BNS = {
    302: "101",
    356: "304",
    379: "303",
    380: "305",
    392: "309",
    406: "316",
    411: "317",
    420: "318",
    498: "84",
}

SYNTHETIC_MARKER = "SYNTHETIC-DEMO-ONLY"
