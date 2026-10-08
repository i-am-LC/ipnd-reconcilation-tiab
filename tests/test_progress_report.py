"""
Unit tests for progress report generation and count accuracy.
"""

from pathlib import Path

from odf.opendocument import load
from odf.table import TableCell, TableRow
from odf.text import P
import pandas as pd

from main import generate_progress_report, get_unique_phone_count


def test_get_unique_phone_count_various_columns() -> None:
    """Test get_unique_phone_count calculates exact unique phone numbers."""
    assert get_unique_phone_count(None) == 0
    assert get_unique_phone_count(pd.DataFrame()) == 0

    df_service = pd.DataFrame(
        {"Service Number": ["0263301410", "0263301410", "0263301420"]}
    )
    assert get_unique_phone_count(df_service) == 2

    df_phone = pd.DataFrame({"Phone Number": ["0358228011", "0358228012"]})
    assert get_unique_phone_count(df_phone) == 2

    df_public = pd.DataFrame(
        {"Public Number": ["0412345678", "0412345678", "0412345678"]}
    )
    assert get_unique_phone_count(df_public) == 1


def test_generate_progress_report_unique_counts(tmp_path: Path) -> None:
    """Test that generated progress report ODT table contains unique phone counts."""
    template_path = Path("IPND_Reconciliation_Progress_report_template.odt")
    if not template_path.exists():
        return

    # Create dummy results with duplicates to verify unique count is used
    results = {
        "1. Active not in IPND": pd.DataFrame(
            {"Service Number": ["0263301410", "0263301420"]}
        ),
        "2. Active but IPND Disconnected": pd.DataFrame(
            {"Service Number": ["0358228011", "0358228011"]}  # 1 unique
        ),
        "3. Disconnected but IPND Connected": pd.DataFrame(
            {"Phone Number": ["0731234567"]}
        ),
        "4. IPND Connected not in CSP": pd.DataFrame(
            {"Public Number": ["0881234567", "0881234567", "0881234568"]}  # 2 unique
        ),
        "5. IPND Conflicts": pd.DataFrame(
            {"Public Number": ["0412345678", "0412345679"]}
        ),
    }

    output_dir = tmp_path / "Output"
    generate_progress_report(
        results=results,
        template_path=str(template_path),
        output_dir=str(output_dir),
    )

    odt_files = list(output_dir.glob("*.odt"))
    assert len(odt_files) == 1

    doc = load(str(odt_files[0]))
    table = doc.text.getElementsByType(TableRow)[0].parentNode
    rows = list(table.getElementsByType(TableRow))

    # Row 1 (Cat 1): 2 unique
    cat1_cells = rows[1].getElementsByType(TableCell)
    cat1_p = cat1_cells[3].getElementsByType(P)
    assert any("2" in str(p) for p in cat1_p)

    # Row 2 (Cat 2): 1 unique (from 2 rows with same number)
    cat2_cells = rows[2].getElementsByType(TableCell)
    cat2_p = cat2_cells[3].getElementsByType(P)
    assert any("1" in str(p) for p in cat2_p)

    # Row 4 (Cat 4): 2 unique (from 3 rows with 2 unique numbers)
    cat4_cells = rows[4].getElementsByType(TableCell)
    cat4_p = cat4_cells[3].getElementsByType(P)
    assert any("2" in str(p) for p in cat4_p)
