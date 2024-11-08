from pyDataverse.api import NativeApi

# ---- Authenticate to Dataverse ---- #
BASE_URL = "https://demo.dataverse.org"  # URL for the specific Dataverse installation
API_TOKEN = "XXX"  # Your API-Token for DV demo installation

# ---- Connect to Dataverse API ---- #
api = NativeApi(BASE_URL, API_TOKEN)
resp = api.get_info_version()
print(f"HTTP Status: {resp.status_code}")

# ---- Provide DOI ---- #
DOI = "https://doi.org/10.70122/FK2/TWGB7R"  # modified dvdspid (DRAFT)
# DOI = "https://doi.org/10.70122/FK2/6RSJP8"  # published dataset

# ---- Get Dataset ---- #
try:
    dataset = api.get_dataset(DOI)
    print(f"HTTP Status: {dataset.status_code} -- Dataset is published")
    # print(f"Dataset metadata: {dataset.json()}")
except:
    print("Dataset is not published")

# -------> Phase-2: Get additional metadata (and checksum?) and save to iRODS?
