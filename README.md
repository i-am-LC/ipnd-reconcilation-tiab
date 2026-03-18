# IPND Reconciliation Project


## Overview

This project is designed to reconcile IPND (Integrated Public Number Database) records with CSP (Communications Service Provider) active service and disconnected service reports. The goal is to identify discrepancies between the IPND records and the CSP data.
The Integrated Public Number Database (IPND) is a centralised database that contains the record of each telephone number issued by Carriage Service Providers (CSPs) to their customers in Australia.

### Prerequisites

* Python 3.x installed on your machine
* A virtual environment set up in the project root directory (`venv`)
* `pip` installed with the required packages (see `requirements.txt`)

### Running the Project

1. Run the following commands to create a new virtual environment and install dependencies:

    `python3 -m venv venv`<br>
    `source venv/bin/activate`<br>
    `pip install -r requirements.txt`
2. Place the necessary CSV files in the InputCSVs directory (see below)
3. Run the project using the following command:
```python3 main.py```

### Input Files
To run the project, you need to have three CSV files in the InputCSVs directory and one template file in the project root:

**CSV files (InputCSVs/ directory):**
* AllActiveServices.csv: The CSP active service report (download from Octane)
* AllDisconnectedServices.csv: The CSP disconnected service report (download from Octane)
* IPNDSnapshotRecon.csv: The IPND snapshot reconciliation report (download from Octane)

**Template file (project root):**
* IPND_Reconciliation_Progress_report_template.odt: Progress report template used to generate the populated output document

### Output Files
The project generates two output files in the Output directory:

**1. IPND_Results.xlsx**
   Excel file containing detailed reconciliation results across five sheets:

1. **1. Active not in IPND**: Phone numbers that are ACTIVE in your system but NOT PRESENT in IPND. Action: Arrange to submit your data to IPND to correct the misalignment.

2. **2. Active but IPND Disconnected**: Phone numbers that are ACTIVE (connected) in your system but DISCONNECTED in IPND. Action: Confirm if service status is genuinely active. If so, correct IPND record to Connected.

3. **3. Disconnected but IPND Connected**: Phone numbers that are INACTIVE (disconnected) in your system but CONNECTED in IPND. Action: Investigate if service is genuinely inactive. If so, correct IPND record to Disconnected.

4. **4. IPND Connected not in CSP**: Phone numbers that are NOT PRESENT in your system but CONNECTED in IPND. Action: Investigate if you genuinely have no record. If so, correct IPND record to Disconnected.

5. **5. IPND Conflicts**: Records where IPND status and termination date are inconsistent:
   - Status='C' (Connected) with a non-null termination date (should not have termination date if connected)
   - Status='D' (Disconnected) with a null termination date (should have termination date if disconnected)
   These represent data quality issues in IPND that require investigation before reconciliation.

**2. IPND_Reconciliation_Progress_report_YYYY-MM-DD.odt**
   Progress report document automatically populated from the template file. This document includes:
   - Operation ID "558" populated in Column 1 for all 5 data rows
   - Today's date (YYYY-MM-DD format) in the "Date misalignment identified" column for all categories
   - Count of misaligned services for each of the 5 reconciliation categories
   - Category 5 row added for IPND conflicts requiring investigation
   - Preserved formatting and structure from the original template

   The output filename includes the current date (e.g., IPND_Reconciliation_Progress_report_2026-03-19.odt) for version control.

### Error Handling and Validation

The script includes comprehensive error handling and validation:

* Validates that all required CSV files exist before processing
* Checks that required columns are present in each input file
* Validates that input files contain data after reading
* **Phone number validation against Australian standards:**
  - Only includes numbers starting with 02, 03, 04, 07, or 08 (valid Australian prefixes)
  - Excludes service numbers (13, 1300, 1800, 1900) and non-numeric data
  - Enforces exactly 10-digit format with leading zeros preserved
  - IPND numbers padded with leading zeros for consistency
* Provides clear error messages for missing files, missing columns, or malformed data
* Gracefully handles file I/O errors with informative messages
* Uses vectorized pandas operations for efficient processing
* Includes input confirmation prompt to verify file readiness

### Assumptions
This project assumes that:

* The input CSV files follow the format from Octane reports (Skip 2 rows for headers)
* **Phone number validation:**
  - Only Australian phone numbers are processed (02, 03, 04, 07, 08 prefixes)
  - Mobile numbers use 04 prefix with exactly 10 digits
  - Landlines use 02, 03, 07, 08 prefixes with exactly 10 digits
  - Service numbers (13, 1300, 1800, 1900) and other non-phone data are excluded
  - IPND data may be missing leading zeros and will be automatically padded
* IPND reconciliation logic aligns with CSP business requirements
* Output Excel files preserve phone numbers as strings to maintain leading zeros