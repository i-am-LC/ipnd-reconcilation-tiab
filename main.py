"""
IPND Reconciliation Script

This script reconciles CSP (Communications Service Provider) active/disconnected service
records with IPND (Integrated Public Number Database) records to identify discrepancies.

Input files required:
- InputCSVs/AllActiveServices.csv: Active services from carrier system
- InputCSVs/AllDisconnectedServices.csv: Disconnected services (last 12 months) from carrier
- InputCSVs/IPNDSnapshotRecon.csv: Current IPND records

Output:
- Output/IPND_Results.xlsx with 5 reconciliation categories
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
import re
from odf.opendocument import load
from odf.table import TableRow, TableCell
from odf.text import P


# Constants for required columns
REQUIRED_COLUMNS: Dict[str, List[str]] = {
    'AllActiveServices.csv': ['Service ID', 'Service Number'],
    'AllDisconnectedServices.csv': ['Phone Number'],
    'IPNDSnapshotRecon.csv': [
        'Public Number',
        'Terminated Date',
        'Service Status Code'
    ]
}

# Non-phone number service IDs to filter out
NON_PHONE_SERVICE_IDS = ['OT', 'DT', 'TX', 'NN']


def validate_input_files() -> None:
    """
    Validate that all required CSV files exist and contain required columns.

    Raises:
        FileNotFoundError: If any required CSV file is missing
        ValueError: If required columns are missing from any file
        pd.errors.EmptyDataError: If any CSV file is empty
    """
    print("Validating input files...")
    
    for filename, required_cols in REQUIRED_COLUMNS.items():
        file_path = Path('InputCSVs') / filename
        
        # Check file exists
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file not found: InputCSVs/{filename}\n"
                f"Please ensure all required files are in the InputCSVs directory."
            )
        
        # Load and validate columns
        try:
            df = pd.read_csv(file_path, skiprows=2)
        except pd.errors.EmptyDataError:
            raise pd.errors.EmptyDataError(
                f"File is empty or malformed: InputCSVs/{filename}"
            )
        except Exception as e:
            raise Exception(
                f"Error reading {filename}: {str(e)}"
            )
        
        # Check dataframe is not empty
        if df.empty:
            raise ValueError(f"No data found in {filename} after reading")
        
        # Check required columns exist
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"{filename} is missing required columns: {', '.join(missing_cols)}\n"
                f"Required columns: {', '.join(required_cols)}\n"
                f"Found columns: {', '.join(df.columns.tolist())}"
            )
    
    print("✓ All files validated successfully")


def load_data() -> Dict[str, pd.DataFrame]:
    """
    Load all three CSV files into pandas DataFrames.

    Returns:
        Dict containing DataFrames for active, disconnected, and IPND reports

    Raises:
        Exception: If any file loading fails
    """
    print("Loading data files...")
    
    try:
        active_service_report: pd.DataFrame = pd.read_csv(
            'InputCSVs/AllActiveServices.csv', skiprows=2
        )
        discon_service_report: pd.DataFrame = pd.read_csv(
            'InputCSVs/AllDisconnectedServices.csv', skiprows=2
        )
        ipnd_report: pd.DataFrame = pd.read_csv(
            'InputCSVs/IPNDSnapshotRecon.csv', skiprows=2
        )
        
        print(f"✓ Loaded {len(active_service_report)} active services")
        print(f"✓ Loaded {len(discon_service_report)} disconnected services")
        print(f"✓ Loaded {len(ipnd_report)} IPND records")
        
        return {
            'active': active_service_report,
            'disconnected': discon_service_report,
            'ipnd': ipnd_report
        }
    except Exception as e:
        print(f"✗ Error loading data: {str(e)}")
        raise


def normalize_phone_numbers(
    active_service_report: pd.DataFrame,
    discon_service_report: pd.DataFrame
) -> pd.DataFrame:
    """
    Normalize and validate phone numbers with strict Australian phone number rules.

    Validation rules:
    - Numbers must be exactly 10 digits
    - Must start with valid Australian prefix: 02, 03, 04, 07, or 08
    - Leading zero preserved (Australian format requirement)
    - EXCLUDED: Service numbers (13, 1300, 1800, 1900) and other non-phone numbers

    Args:
        active_service_report: DataFrame of active services with 'Service Number' column
        discon_service_report: DataFrame of disconnected services with 'Phone Number' column

    Returns:
        Updated DataFrames with validated phone numbers only
    """
    print("Normalizing and validating phone numbers...")
    
    # Valid Australian phone number pattern:
    # - 02, 03: Landlines (NSW/ACT, VIC/TAS)
    # - 04: Mobile numbers
    # - 07: Landlines (QLD)
    # - 08: Landlines (WA/SA/NT)
    phone_pattern = r'^(04|02|03|07|08)\d{8}$'
    
    # Process active services
    active_before = len(active_service_report)
    active_service_report['Service Number'] = (
        active_service_report['Service Number']
        .astype(str)
    )
    
    # Validate with strict Australian phone pattern
    valid_mask_active = (
        active_service_report['Service Number']
        .str.match(phone_pattern, na=False)
    )
    active_service_report = active_service_report[valid_mask_active].copy()
    
    active_filtered = active_before - len(active_service_report)
    print(f"✓ Filtered {active_filtered} invalid phone numbers from active services")
    print(f"✓ Retained {len(active_service_report)} valid Australian phone numbers")
    
    # Process disconnected services
    discon_before = len(discon_service_report)
    discon_service_report['Phone Number'] = (
        discon_service_report['Phone Number']
        .astype(str)
    )
    
    # Validate with strict Australian phone pattern
    valid_mask_discon = (
        discon_service_report['Phone Number']
        .str.match(phone_pattern, na=False)
    )
    discon_service_report = discon_service_report[valid_mask_discon].copy()
    
    discon_filtered = discon_before - len(discon_service_report)
    print(f"✓ Filtered {discon_filtered} invalid phone numbers from disconnected services")
    print(f"✓ Retained {len(discon_service_report)} valid Australian phone numbers")
    
    return active_service_report, discon_service_report


def normalize_ipnd_numbers(ipnd_report: pd.DataFrame) -> pd.DataFrame:
    """
    Pad IPND Public Numbers with leading zero to match Australian format.

    IPND data comes without leading zeros. This function pads valid 9-digit
    numbers to ensure they match Australian phone number format with leading zero.

    Args:
        ipnd_report: DataFrame of IPND records with 'Public Number' column

    Returns:
        DataFrame with padded phone numbers
    """
    print("Normalizing IPND phone numbers...")
    
    # Convert to string and pad with zeros to 10 digits
    ipnd_report['Public Number'] = (
        ipnd_report['Public Number']
        .astype(str)
        .str.zfill(10)
    )
    
    print(f"✓ Normalized {len(ipnd_report)} IPND records with leading zeros")
    
    return ipnd_report


def filter_non_phone_services(
    active_service_report: pd.DataFrame
) -> pd.DataFrame:
    """
    Remove non-phone number services from active service report.

    Filters out services with Service ID in:
    - 'OT': Other
    - 'DT': Data service
    - 'TX': Text service
    - 'NN': Non-numeric

    Args:
        active_service_report: DataFrame of active services

    Returns:
        Filtered DataFrame containing only phone services
    """
    print("Filtering non-phone number services...")
    
    non_phone_mask = active_service_report['Service ID'].isin(NON_PHONE_SERVICE_IDS)
    active_service_report = active_service_report[~non_phone_mask].copy()
    
    print(f"✓ Removed {non_phone_mask.sum()} non-phone services") 
    
    return active_service_report


def process_reconciliation(
    active_service_report: pd.DataFrame,
    discon_service_report: pd.DataFrame,
    ipnd_report: pd.DataFrame
) -> Dict[str, pd.DataFrame]:
    """
    Process all 5 IPND reconciliation categories.

    Categories:
    1: Active services not in IPND
    2: Active services marked as disconnected in IPND
    3: Disconnected services marked as connected in IPND
    4: IPND connected records not in CSP system
    5: IPND records with conflicting status/termination data

    Args:
        active_service_report: DataFrame of active services
        discon_service_report: DataFrame of disconnected services
        ipnd_report: DataFrame of IPND records

    Returns:
        Dict mapping category names to their DataFrames
    """
    print("Processing reconciliation categories...")
    
    # Normalize IPND numbers (pad with leading zero)
    ipnd_report = normalize_ipnd_numbers(ipnd_report)
    
    # Ensure string types for comparison
    ipnd_report['Public Number'] = ipnd_report['Public Number'].astype(str)
    active_service_report['Service Number'] = (
        active_service_report['Service Number'].astype(str)
    )
    discon_service_report['Phone Number'] = (
        discon_service_report['Phone Number'].astype(str)
    )
    
    results = {}
    
    # Category 5: Identify IPND data conflicts FIRST
    # Records with inconsistent status and termination date
    ipnd_conflicts = ipnd_report[
        ((ipnd_report['Terminated Date'].notnull()) &
         (ipnd_report['Service Status Code'] == 'C')) |
        ((ipnd_report['Terminated Date'].isnull()) &
         (ipnd_report['Service Status Code'] == 'D'))
    ].copy()
    results['5. IPND Conflicts'] = ipnd_conflicts
    print(f"✓ Category 5: Found {len(ipnd_conflicts)} IPND conflicts")
    
    # Remove conflicts from IPND for subsequent processing
    ipnd_report_clean = ipnd_report[~ipnd_report.index.isin(ipnd_conflicts.index)].copy()
    
    # Category 1: Active services not present in IPND
    active_not_in_ipnd = active_service_report[
        ~active_service_report['Service Number'].isin(ipnd_report_clean['Public Number'])
    ].copy()
    results['1. Active not in IPND'] = active_not_in_ipnd
    print(f"✓ Category 1: Found {len(active_not_in_ipnd)} active services not in IPND")
    
    # Category 2: Active services with disconnected status in IPND
    # IPND disconnected: has termination date OR status='D'
    ipnd_disconnected = ipnd_report_clean[
        (ipnd_report_clean['Terminated Date'].notnull()) |
        (ipnd_report_clean['Service Status Code'] == 'D')
    ]
    active_but_ipnd_disconnected = active_service_report[
        active_service_report['Service Number'].isin(ipnd_disconnected['Public Number'])
    ].copy()
    results['2. Active but IPND Disconnected'] = active_but_ipnd_disconnected
    print(f"✓ Category 2: Found {len(active_but_ipnd_disconnected)} active with IPND disconn")
    
    # Category 3: Disconnected services with connected status in IPND
    # IPND connected: no termination date AND status='C' (strict definition)
    ipnd_connected = ipnd_report_clean[
        (ipnd_report_clean['Terminated Date'].isnull()) &
        (ipnd_report_clean['Service Status Code'] == 'C')
    ]
    
    # Clean disconnected report: remove services that appear in active (plan changes)
    cleaned_discon_report = discon_service_report[
        ~discon_service_report['Phone Number'].isin(
            active_service_report['Service Number']
        )
    ].copy()
    
    discon_but_ipnd_connected = cleaned_discon_report[
        cleaned_discon_report['Phone Number'].isin(ipnd_connected['Public Number'])
    ].copy()
    results['3. Disconnected but IPND Connected'] = discon_but_ipnd_connected
    print(f"✓ Category 3: Found {len(discon_but_ipnd_connected)} disconn with IPND conn")
    
    # Category 4: IPND connected records not in CSP system
    ipnd_connected_not_in_csp = ipnd_connected[
        ~ipnd_connected['Public Number'].isin(active_service_report['Service Number'])
    ].copy()
    results['4. IPND Connected not in CSP'] = ipnd_connected_not_in_csp
    print(f"✓ Category 4: Found {len(ipnd_connected_not_in_csp)} IPND conn not in CSP")
    
    return results


def write_output(results: Dict[str, pd.DataFrame]) -> None:
    """
    Write all reconciliation results to an Excel file with multiple sheets.

    Converts phone number columns to string to preserve leading zeros.

    Args:
        results: Dict mapping sheet names to DataFrames
    """
    print("Writing output to Excel file...")
    
    try:
        with pd.ExcelWriter("Output/IPND_Results.xlsx") as writer:
            for sheet_name, df in results.items():
                # Convert phone number columns to string as object to preserve leading zeros
                if len(df) > 0:
                    for col in df.columns:
                        if 'Number' in col or 'Phone' in col:
                            df[col] = df[col].astype(str)
                
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print("✓ Output written to Output/IPND_Results.xlsx")
    except Exception as e:
        print(f"✗ Error writing output: {str(e)}")
        raise


def generate_progress_report(
    results: Dict[str, pd.DataFrame],
    template_path: str = 'IPND_Reconciliation_Progress_report_template.odt',
    output_dir: str = 'Output'
) -> None:
    """
    Generate a populated IPND Reconciliation Progress Report from template.

    Copies the template, populates it with reconciliation counts and today's date,
    and saves it with a timestamped filename.

    Args:
        results: Dict mapping category names to DataFrames with reconciliation results
        template_path: Path to the ODT template file
        output_dir: Directory where the output file should be saved
    """
    print("Generating progress report...")
    
    try:
        # Load the template
        if not Path(template_path).exists():
            raise FileNotFoundError(
                f"Template file not found: {template_path}"
            )
        
        doc = load(template_path)
        
        # Get the table (should be Table1)
        tables = doc.text.getElementsByType(TableRow)[0].parentNode
        
        # Get all rows
        rows = list(tables.getElementsByType(TableRow))
        
        # Data rows start at index 1 (row 2 of the table, index 0 is header)
        # The template has 4 data rows (indices 1-4), we need to add a 5th for Category 5
        
        # Today's date in YYYY-MM-DD format
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        # Category 5 description
        category_5_description = (
            "Total number of customer records in IPND with inconsistent "
            "status and termination data requiring investigation"
        )
        
        # Add Category 5 row if it doesn't exist
        if len(rows) <= 5:  # header + 4 data rows
            new_row = TableRow()
            for i in range(10):  # 10 columns
                cell = TableCell()
                cell.addElement(P(text=''))
                new_row.addElement(cell)
            tables.addElement(new_row)
            rows = list(tables.getElementsByType(TableRow))
        
        # Count lookup (sheet_name -> count)
        category_counts = {
            '1. Active not in IPND': len(results['1. Active not in IPND']),
            '2. Active but IPND Disconnected': len(results['2. Active but IPND Disconnected']),
            '3. Disconnected but IPND Connected': len(results['3. Disconnected but IPND Connected']),
            '4. IPND Connected not in CSP': len(results['4. IPND Connected not in CSP']),
            '5. IPND Conflicts': len(results['5. IPND Conflicts'])
        }
        
        # Populate data rows (indices 1-5, skipping header at index 0)
        for i, row_index in enumerate(range(1, 6)):
            row = rows[row_index]
            cells = row.getElementsByType(TableCell)
            
            if len(cells) < 10:
                continue  # Skip malformed rows
            
            # Column 2 (index 1): Date misalignment identified
            date_cell = cells[1]
            # Clear existing content and add new date
            for child in list(date_cell.childNodes):
                date_cell.removeChild(child)
            date_cell.addElement(P(text=today_date))
            
            # Column 4 (index 3): Total misaligned services
            count_cell = cells[3]
            category_order = ['1. Active not in IPND', '2. Active but IPND Disconnected',
                             '3. Disconnected but IPND Connected', '4. IPND Connected not in CSP',
                             '5. IPND Conflicts']
            if i < len(category_order):
                category_name = category_order[i]
                count = category_counts.get(category_name, 0)
                # Clear existing content and add new count
                for child in list(count_cell.childNodes):
                    count_cell.removeChild(child)
                count_cell.addElement(P(text=str(count)))
            
            # Category 5: Set description in Column 3 (index 2)
            if i == 4:  # Category 5 row (5th data row, index 4 in 0-based)
                desc_cell = cells[2]
                # Clear existing content and add new description
                for child in list(desc_cell.childNodes):
                    desc_cell.removeChild(child)
                desc_cell.addElement(P(text=category_5_description))
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate timestamped filename
        output_filename = f"IPND_Reconciliation_Progress_report_{datetime.now().strftime('%Y-%m-%d')}.odt"
        output_path = Path(output_dir) / output_filename
        
        # Save the document
        doc.save(str(output_path))
        
        print(f"✓ Progress report created: {output_path}")
        
    except FileNotFoundError as e:
        print(f"✗ Template not found: {str(e)}")
        raise
    except Exception as e:
        print(f"✗ Error generating progress report: {str(e)}")
        raise


def main() -> None:
    """
    Main execution function for IPND reconciliation.

    Workflow:
    1. Display instructions and confirm file readiness
    2. Validate input files
    3. Load data
    4. Filter non-phone services
    5. Normalize phone numbers
    6. Process reconciliation (5 categories)
    7. Write results to Excel
    8. Generate progress report from template
    """
    # Display instructions
    instructions = [
        "Ensure you have the below files saved within this project's 'InputCSVs' DIR",
        "1. 'AllActiveServices.csv' report pulled from Octane Service reports.",
        "2. 'AllDisconnectedServices.csv' report pulled from Octane Service reports.",
        "3. 'IPNDSnapshotRecon.csv' report pulled from Octane Management reports."
    ]
    
    for i, instruction in enumerate(instructions, start=1):
        print(f"* {instruction}")
    
    print("###########################################")
    print("Has the above been completed? Y/N")
    file_conf = input()
    
    while file_conf != "Y":
        print("Has the above been completed? Y/N")
        file_conf = input()
    
    print("\nRunning script, please wait.")
    print("Once complete you'll find 'IPND_Results.xlsx' in the Output directory.\n")
    
    try:
        # Validate and load data
        validate_input_files()
        data = load_data()
        
        # Preprocess data
        active_service_report = filter_non_phone_services(data['active'])
        active_service_report, discon_service_report = normalize_phone_numbers(
            active_service_report,
            data['disconnected']
        )
        ipnd_report = data['ipnd']
        
        # Process reconciliation
        results = process_reconciliation(
            active_service_report,
            discon_service_report,
            ipnd_report
        )
        
        # Write output
        write_output(results)
        
        # Generate progress report
        generate_progress_report(
            results=results,
            template_path='IPND_Reconciliation_Progress_report_template.odt',
            output_dir='Output'
        )
        
        print("\n" + "="*50)
        print("RECONCILIATION COMPLETE")
        print("="*50)
        print(f"\nTotal records in each category:")
        for sheet_name, df in results.items():
            print(f"  {sheet_name}: {len(df):,}")
        
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user.")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\n✗ {str(e)}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n✗ {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()