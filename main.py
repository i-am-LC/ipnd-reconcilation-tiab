import pandas as pd
import numpy as np
import re

print("####################################################################")
print("# Ensure you have the below files saved within this projects 'InputCSVs' DIR ")
print("# 1. 'AllActiveServices.csv' report pulled from Octane Service reports.")
print("# 2. 'AllDisconnectedServices.csv' report pulled from Octane Service reports.")
print("# 3. 'IPNDSnapshotRecon.csv' report pulled from Octane Management reports. ")
print("####################################################################")
print("Has the above been completed? Y/N  ")
file_conf = input()

while file_conf != "Y":
    print("Has the above been completed? Y/N  ")
    file_conf = input()

print("Running script, please wait.")
print("Once complete you'll find 'IPND_Results.xlsx' sheet in your directory.")


# Load in All Active Service report CSV file.
active_service_report = pd.read_csv('InputCSVs/AllActiveServices.csv', skiprows=2)
# Load disconnection report
discon_service_report = pd.read_csv('InputCSVs/AllDisconnectedServices.csv', skiprows=2)
# Load IPND report
ipnd_report = pd.read_csv('InputCSVs/IPNDSnapshotRecon.csv', skiprows=2)

# Drop non phone number services from active service report.
index_names = active_service_report[
    (active_service_report['Service ID'] == 'OT') | 
    (active_service_report['Service ID'] == 'DT') | 
    (active_service_report['Service ID'] == 'TX') | 
    (active_service_report['Service ID'] == 'NN')
    ].index
active_service_report.drop(index_names, inplace=True)


for i in active_service_report.index:
    phone_num_regex = re.compile(r'^(?!1300|1800)(\d{10})$')
    match_object = phone_num_regex.search(active_service_report['Service Number'][i])
    if match_object:

        phone_num = match_object.group().lstrip("0")

        active_service_report['Service Number'] = active_service_report['Service Number'].replace(
            to_replace=active_service_report['Service Number'][i], value=phone_num)
    else:
        active_service_report.drop(index=i, inplace=True)

ipnd_report['Public Number'] = ipnd_report['Public Number'].astype(str)
active_service_report['Service Number'] = active_service_report['Service Number'].astype(str)

for i in discon_service_report.index:
    phone_num_regex = re.compile(r'^(?!1300|1800)(\d{10})$')
    match_object = phone_num_regex.search(discon_service_report['Phone Number'][i])
    if match_object:

        phone_num = match_object.group().lstrip("0")

        discon_service_report['Phone Number'] = discon_service_report['Phone Number'].replace(
            to_replace=discon_service_report['Phone Number'][i], value=phone_num)

'''
Total number of Numbers associated with a CSP’s active 
service that do not have a corresponding customer
record in the IPND;
'''
# Filter where an IPND record IS NOT in the Active Service list.
in_IPND_not_active_service = ipnd_report[~ipnd_report['Public Number'].isin(active_service_report['Service Number'])]

# Filter for those in Active service but NOT IN IPND
in_active_service_not_IPND = active_service_report[~active_service_report['Service Number'].isin(ipnd_report['Public Number'])]

'''
Total number of Numbers associated with a CSP’s active service for which 
the corresponding customer record in the IPND has a 
‘disconnected’ status
'''
# Services with discon date in IPND
# ipnd_disconnected_date_df = ipnd_report[~ipnd_report['Terminated Date'].isnull()]
# Services with disconnected ('D') service status in IPND
# ipnd_disconnected_status_df = ipnd_report[ipnd_report['Service Status Code'] == 'D']
# Services with either a disconnected status or terminated date.
ipnd_disconnected = ipnd_report[(~ipnd_report['Terminated Date'].isnull()) | (ipnd_report['Service Status Code'] == 'D')]

active_service_in_IPND_discon = active_service_report[active_service_report['Service Number'].isin(
    ipnd_disconnected['Public Number'])]

'''
Total number of customer records associated with CSP with 
a ‘connected’ status in the IPND for which 
the Number is designated as ‘disconnected’ in CSPs Customer System
'''
ipnd_connected = ipnd_report[(ipnd_report['Terminated Date'].isnull()) & (ipnd_report['Service Status Code'] == 'C')]
"""
Octane lists services with a plan change as disconnected in the Disconnected Service report. 
Remove any reference to a disconnected service if it has an active service in the Active Service report.
"""
cleaned_discon_service_report = discon_service_report[~discon_service_report['Phone Number'].isin(active_service_report['Service Number'])]

disconected_but_connected_in_ipnd = cleaned_discon_service_report[cleaned_discon_service_report['Phone Number'].isin(ipnd_connected['Public Number'])]

'''
Total number of customer records associated with CSP with 
a ‘connected’ status in the IPND which 
are not present in CSPs Customer System.
'''
ipnd_connected = ipnd_report[(ipnd_report['Terminated Date'].isnull()) | (ipnd_report['Service Status Code'] == 'C')]

in_connected_IPND_not_in_active_services = ipnd_connected[~ipnd_connected['Public Number'].isin(active_service_report['Service Number'])]

# create a excel writer object
with pd.ExcelWriter("Output/IPND_Results.xlsx") as writer:
   
    # use to_excel function and specify the sheet_name and index
    # to store the dataframe in specified sheet
    in_active_service_not_IPND.to_excel(writer, sheet_name="ActiveServices != IPND", index=False)
    active_service_in_IPND_discon.to_excel(writer, sheet_name="ActiveServices in IPND D", index=False)
    disconected_but_connected_in_ipnd.to_excel(writer, sheet_name="DisconServices in IPND C", index=False)
    in_connected_IPND_not_in_active_services.to_excel(writer, sheet_name="ActiveServices != IPND C", index=False)
