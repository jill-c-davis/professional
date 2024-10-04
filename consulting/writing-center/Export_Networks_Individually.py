#!/usr/bin/env python
# coding: utf-8

# ### Step 1: Import Dependencies
# - The application relies on two imported modules:
#   - `requests`: To send a GET request to the API.
#   - `csv`: To export the results to a csv file
#   - `pandas`: For documentation purposes, I am using pandas to convert the initial csv into a data frame

# In[26]:


import requests
import csv
import pandas as pd


# ### Step 2: Export Organization IDs to a CSV based on the Organization's Name
# - The function `export_org_id_to_csv` accepts two arguments:
#   - `api_url_1`: The initial URL to make the API request.
#   - `filename`: The name of the output CSV file, with a default value of `"organization_ids.csv"`.
# - Example value for `api_url_1`: "https://cmsmanapi.anthem.com/fhir/cms_mandate/mcd/Organization?name=Cottage%20Hospital"

# In[27]:


def export_org_id_to_csv(api_url_1, filename="organization_ids.csv"):
    headers = {"Accept": "application/fhir+json"}
    all_entries = []

    while api_url_1:
        response = requests.get(api_url_1, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Collect all entries
            all_entries.extend(data.get('entry', []))
            
            # Check for the next page
            api_url_1 = None
            for link in data.get('link', []):
                if link.get('relation') == 'next':
                    api_url_1 = link.get('url')
                    break

        else:
            print(f"Failed to retrieve data: {response.status_code}")
            break

    # Export to CSV
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write header row
        writer.writerow(["id", "name", "identifiers"])
        
        # Write data rows
        for entry in all_entries:
            organization = entry.get('resource', {})
            org_id = organization.get('id', '')
            org_name = organization.get('name', '')
            
            # Extract all identifiers
            identifiers = organization.get('identifier', [])
            identifier_values = [identifier.get('value', '') for identifier in identifiers]
            
            # Join all identifier values into a single string, separated by commas
            identifier_str = ", ".join(identifier_values)
            
            writer.writerow([org_id, org_name, identifier_str])

    print(f"Data has been exported to {filename}")


# In[28]:


# API URL
api_url_1 = "https://cmsmanapi.anthem.com/fhir/cms_mandate/mcd/Organization?name=Cottage%20Hospital"
export_org_id_to_csv(api_url_1)


# - In this example, calling thefunction `export_org_id_to_csv` will find any JSON entries with a name of "Cottage Hospital" and export the following fields into a CSV:
#     - `id`: This is the 6-digit ID for the organization
#     - `name`: This is the name of the organization
#     - `identifiers`: These are two values, separated by a comma, indicating the associated Provider Number and NPI for the organization.
# - The results for Cottage Hospital are printed below

# In[29]:


df = pd.read_csv("organization_ids.csv")
print(df)


# ### Step 3: Find Associated Networks based on the Organization's ID
# - The function `fetch_all_data` accepts one argument:
#   - `api_url_2`: This is the url used to make the second API request to get associated networks.
#       - Example value for `api_url_2`: "https://cmsmanapi.anthem.com/fhir/cms_mandate/mcd/PractitionerRole?organization=Organization/484295"
#       - `api_url_2` is based on the Organization ID taken from the `export_org_id_to_csv` function's output

# In[30]:


# Function to fetch all paginated data from the API
def fetch_all_data(api_url_2):
    all_data = []
    while api_url_2:
        response = requests.get(api_url_2)
        if response.status_code == 200:
            data = response.json()
            if 'entry' in data:
                all_data.extend(data['entry'])
            # Get the next page link from the 'link' section
            api_url_2 = None  # Default to None, meaning no more pages
            for link in data.get('link', []):
                if link['relation'] == 'next':
                    api_url_2 = link['url']
                    break
        else:
            raise Exception(f"Failed to fetch data. Status code: {response.status_code}")
    return all_data


# - The function `extract_networks` accepts one argument:
#   - `data`: This is the the data we collected from the initial GET request in the `fetch_all_data` function
# - The function iterates through each JSON entry found from api_url_2 and returns the Practitioner Role ID and Network for each entry

# In[31]:


# Function to extract associated networks from the data
def extract_networks(data):
    networks = []
    for entry in data:
        practitioner_role = entry['resource']
        for ext in practitioner_role.get('extension', []):
            if ext['url'] == "http://hl7.org/fhir/us/davinci-pdex-plan-net/StructureDefinition/network-reference":
                value_reference = ext.get('valueReference', {})
                networks.append({
                    'practitionerRole': practitioner_role['id'],
                    'network': value_reference.get('display', value_reference.get('reference', 'Unknown'))
                })
    return networks


# In[32]:


api_url_2 = "https://cmsmanapi.anthem.com/fhir/cms_mandate/mcd/PractitionerRole?organization=Organization/484295"


# ### Step 4: Write to CSV
# - Using `fetch_all_data` and `extract_networks`, we now have enough information to write Cottage Hospital's associated networks to a csv file:

# In[33]:


# Fetch all data from the API
try:
    data = fetch_all_data(api_url_2)
    
    # Extract associated networks
    networks = extract_networks(data)
    
    # Export the networks to a CSV file
    with open('associated_networks.csv', 'w', newline='') as csvfile:
        fieldnames = ['practitionerRole', 'network']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for network in networks:
            writer.writerow(network)
    
    print(f"Associated networks have been saved to 'associated_networks.csv'")
except Exception as e:
    print(e)


# - We now have the Practitioner Role ID and associated Network for Cottage Hospital

# In[34]:


df = pd.read_csv("associated_networks.csv")
print(df)


# - Typically, I will remove the duplicate networks in Excel, but this is also possible in pandas as shown below.

# In[35]:


df_unique = df.drop_duplicates(subset=['network'])
print(df_unique)

