# import modules
import os, os.path
from irods.session import iRODSSession
from irods.models import Collection, DataObject, DataObjectMeta
from irods.column import Criterion
from pyDataverse.api import NativeApi

# --- Authenticate to iRODS --- #
env_file = os.getenv(
    "iRODS_ENVIRONMNET_FILE",
    os.path.expanduser("~/.irods/irods_environment.json"),
)
session = iRODSSession(irods_env_file=env_file)

# --- Files from iRODS zone path + name ---- #
srcPath = "/set/home/datateam_set/iRODS2DV/"
srcObj = "iRODSfile.txt"
# -------> Phase-2: Include iRODS AVU e.g. 'send_to_DVdemo', query based on the metadata and get the required info

# ---- Get Data Object from iRODS ---- #
publishedObj = session.data_objects.get(f"{srcPath}{srcObj}")
print(publishedObj)

# ---- Get Data Object Metadata from iRODS ---- #
lpid = []
qpid = (
    session.query(DataObjectMeta.value)
    .filter(Criterion("=", DataObject.name, srcObj))
    .filter(Criterion("=", DataObjectMeta.name, "dvdspid"))
)
lpid = [item[DataObjectMeta.value] for item in qpid]
print(lpid)

dsPID_complete = str(lpid[0])
print(dsPID_complete)

BASE_URL = "https://demo.dataverse.org"  # URL for the specific Dataverse installation
API_TOKEN = (
    "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"  # Your API-Token for DV demo installation
)

# ---- Connect to Dataverse API ---- #
api = NativeApi(BASE_URL, API_TOKEN)

# User input to continue demo
print("Continue...")
input()

# ---- Freeze Dataset in Dataverse ---- #
print(
    "Pre-requisites to publish Dataset to Dataverse:\n",
    "The license is specified via the private URL",
)
resp = api.publish_dataset(dsPID_complete, release_type="major")  # minor
print(resp.json())

# ---- Save publication Metadata in iRODS ---- #
if resp.status_code == "OK":
    publishedObj.metadata.add("timestampPublished", "2024-03-18")
else:
    print(f"The draft is not published, api status code is {resp.status_code}")

# ---- Clean up iRODS session ---- #
session.cleanup()
