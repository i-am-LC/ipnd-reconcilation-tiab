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
To run the project, you need to have three CSV files in the InputCSVs directory:

* AllActiveServices.csv: The CSP active service report (download from Octane)
* AllDisconnectedServices.csv: The CSP disconnected service report (download from Octane)
* IPNDSnapshotRecon.csv: The IPND snapshot reconciliation report (download from Octane)

### Output File
The project will generate an Excel file called IPND_Results.xlsx in the Output directory. This file contains four sheets:

* ActiveServices != IPND: Discrepancies between active services and IPND records
* ActiveServices in IPND D: Active services present in both CSP and IPND data, with a disconnected status in IPND
* DisconServices in IPND C: Disconnected services present in both CSP and IPND data, with a connected status in IPND
* ActiveServices != IPND C: Discrepancies between active services and IPND records, excluding those already accounted for in the other sheets

### Assumptions
This project assumes that:

* The input CSV files are correctly formatted and contain no errors.
* The reconciliation logic is correct and consistent with the expectations of the CSP data.