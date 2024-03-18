# import modules
import os, os.path
from irods.session import iRODSSession
from pyDataverse.api import NativeApi
from pyDataverse.models import Dataset, Datafile
import json
from pyDataverse.utils import read_file

# --- Files from iRODS zone path + name ---- #
dirSrc = "/set/home/datateam_set/iRODS2DV/"
srcObj = "iRODSfile.txt"
dirTrg = "doc/data/"
# -------> Phase-2: Include iRODS AVU e.g. 'send_to_DVdemo', query based on the metadata and get the required info

# --- Authenticate to iRODS --- #
env_file = os.getenv(
    "iRODS_ENVIRONMNET_FILE",
    os.path.expanduser("~/.irods/irods_environment.json"),
)
session = iRODSSession(irods_env_file=env_file)

# ---- Get User Metadata from iRODS ---- #
print(f"User: {session.username} is authenticated to iRODS")  # [+ email ?]

# ---- Get Data Object from iRODS ---- #
if os.path.exists(f"{dirTrg}{srcObj}"):
    os.remove(f"{dirTrg}{srcObj}")
depositedObj = session.data_objects.get(f"{dirSrc}{srcObj}", f"{dirTrg}{srcObj}")

# ---- Get Data Object Metadata from iRODS ---- #
trgObjvars = vars(depositedObj)
print(
    f"Publish data object with name: {trgObjvars['name']}, object_id: {trgObjvars['id']}, from collection_id: {trgObjvars['collection_id']}"
)

# ---- Authenticate to Dataverse ---- #
BASE_URL = "https://demo.dataverse.org"  # URL for the specific Dataverse installation
API_TOKEN = (
    "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"  # Your API-Token for DV demo installation
)

# ---- Connect to Dataverse API ---- #
api = NativeApi(BASE_URL, API_TOKEN)
resp = api.get_info_version()
print(f"HTTP Status: {resp.status_code}")

# User input to continue demo
print("Continue...")
input()

# ---- Request Metadata Blocks (not in MVW) ---- #
mdBlocks = api.get_metadatablocks()  # List metadata blocks registered in the system.
mdblocks = mdBlocks.json()
json_obj = json.dumps(mdblocks)
with open("doc/metadata/metadataBlocks.json", "w") as outfile:
    outfile.write(json_obj)
del json_obj

# ---- Request Dataset Metadata ---- #
ds = Dataset()  # create a Dataset
ds_md = ds.json()
print(ds_md)  # print dataset metadata
json_obj = json.dumps(eval(ds_md))
with open("doc/metadata/templateDataset.json", "w") as outfile:
    outfile.write(json_obj)  # write in a json file and inspect locally

print(
    f"Dataset metadata (empty): {ds.get()}"
)  # inspect flat dict of all attributes (empty)

# ---- Request Minimum Required Metadata ---- #
print(f"Valid JSON data structure: {ds.validate_json()}")
# Attribute 'author' missing.
# Attribute 'datasetContact' missing.
# Attribute 'dsDescription' missing.
# Attribute 'subject' missing.
# Attribute 'title' missing.

# ---- Inspect the response in the console and write json file mdDataset.json ---- #
# -------> Phase-2: If JSON signifies required metadata (case not found), it can be done automatically.

# User input to continue demo
print("Continue...")
input()

# ---- Read the enriched json file ---- #
# dsMinMD = "doc/metadata/mdDatasetTrial.json"  # example of incomplete metadata
dsMinMD = "doc/metadata/mdDataset.json"
with open(dsMinMD, "r") as inputfile:
    dsMD = json.load(inputfile)  # only for display and update
print(f"The following metadata will be attached:\n {dsMD}")
ds.from_json(read_file(dsMinMD))

# ---- Validate whether a Dataset with this Metadata can be created ---- #
print(f"Valid JSON data structure: {ds.validate_json()}")

# User input to continue demo
print("Continue...")
input()

# -------> Phase-2: Update dataset metadata (Optional)

# ---- Create draft dataset in Dataverse installation ---- #
ds.from_json(read_file(dsMinMD))
resp = api.create_dataset("demo", ds.json())

# ---- Get Status ---- #
dsStatus = resp.json()["status"]
print(f"Upload status: {dsStatus}")

# ---- Get (P)ID ---- #
dsPID = resp.json()["data"]["persistentId"]
print(f"Dataset Persistent Identifier: {dsPID}")
dsID = resp.json()["data"]["id"]
print(f"Dataverse Identifier: {dsID}")

# ---- Get private URL (accessible without login) ---- #
resp = api.create_dataset_private_url(dsPID)
dsPURL = resp.json()["data"]["link"]

# User input to continue demo
print("Continue...")
input()

# ---- Get datafile to be uploaded in Dataset ---- #
df = Datafile()
dfName = f"{dirTrg}{srcObj}"
df.set({"pid": dsPID, "filename": dfName})
df.get()
print(f"This is the datafile metadata:\n {df.json()}")

# ---- Upload file ---- #
resp = api.upload_datafile(dsPID, dfName, df.json())
print(f"This is the response from the datafile upload:\n {resp.json()}")
# Keep additional metadata (see comment below)?
# {'status': 'OK', 'data': {'files': [{'description': '', 'label': 'file1.txt', 'restricted': False, 'version': 1, 'datasetVersionId': 249231, 'dataFile': {'id': 2134919, 'persistentId': '', 'filename': 'file1.txt', 'contentType': 'text/plain', 'friendlyType': 'Plain Text', 'filesize': 90, 'description': '', 'storageIdentifier': 's3://demo-dataverse-org:18e4cadaf8d-8dd8f933923e', 'rootDataFileId': -1, 'md5': 'db32fde37c4b9a22f8963d3f84a61e77', 'checksum': {'type': 'MD5', 'value': 'db32fde37c4b9a22f8963d3f84a61e77'}, 'tabularData': False, 'creationDate': '2024-03-17', 'fileAccessRequest': False}}]}}

# ---- Save draft publication metadata in iRODS ---- #
depositedObj = session.data_objects.get(f"{dirSrc}{srcObj}")
print(depositedObj)

# ---- Save publication Metadata in iRODS ---- #
depositedObj.metadata.add("dvdsid", f"{dsID}")
depositedObj.metadata.add("dvdspid", f"{dsPID}")
depositedObj.metadata.add("dvdspurl", f"{dsPURL}")
depositedObj.metadata.add("dvdsTimestampDraft", "2024-03-18")


# ---- Clean up iRODS session ---- #
session.cleanup()
