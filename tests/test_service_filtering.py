"""
Unit tests for non-phone and preselection service filtering logic.
"""

import pandas as pd

from main import NON_PHONE_SERVICE_IDS, filter_non_phone_services


def test_non_phone_service_ids_contains_preselection() -> None:
    """Test that NON_PHONE_SERVICE_IDS includes T3 and TP."""
    assert "T3" in NON_PHONE_SERVICE_IDS
    assert "TP" in NON_PHONE_SERVICE_IDS
    assert "OT" in NON_PHONE_SERVICE_IDS
    assert "DT" in NON_PHONE_SERVICE_IDS
    assert "TX" in NON_PHONE_SERVICE_IDS
    assert "NN" in NON_PHONE_SERVICE_IDS


def test_filter_removes_t3_and_tp() -> None:
    """Test that filter_non_phone_services removes T3 and TP preselect services."""
    df = pd.DataFrame(
        {
            "Service ID": ["T2", "T3", "TL", "TP", "CP", "OT"],
            "Service Number": [
                "0358228011",
                "0358228011",
                "0263301410",
                "0263301410",
                "0731804993",
                "0390888605",
            ],
            "Description": [
                "ISDN Full",
                "ISDN Preselect",
                "Fixed Line",
                "Fixed Preselect",
                "PBX",
                "Other",
            ],
        }
    )

    filtered = filter_non_phone_services(df)

    retained_ids = set(filtered["Service ID"])
    assert "T3" not in retained_ids
    assert "TP" not in retained_ids
    assert "OT" not in retained_ids
    assert retained_ids == {"T2", "TL", "CP"}
    assert len(filtered) == 3
