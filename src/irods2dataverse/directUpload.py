import requests
import maskpass
import magic
import functions
from irods.data_object import iRODSDataObject

# TO DO: integrate with functions and user-script

### Get information from iRODS ###
# authenticate in iRODS
session = functions.authenticate_iRODS("/home/danai/.irods/irods_environment.json")

# select iRODS object (result of user script query)
src = "/set/home/datateam_set/iRODS2DV/iRODSfileUserScript.txt"
src_dataObj: iRODSDataObject = session.data_objects.get(src)
data = src_dataObj.open("r")

# Get the checksum value from iRODS
chksumRes = src_dataObj.chksum()
chksumVal = chksumRes[5:]  # this is algorithm-specific

# Get the mimetype (from paul, mango portal)
with src_dataObj.open("r") as f:
    blub = f.read(50 * 1024)
    mimeTypeVal = magic.from_buffer(blub, mime=True)

# Get the size of the object
df_size = src_dataObj.size + 1  # add 1 byte

### Configuration specific information ###
# select Dataverse installation (result of user script query)
inp_dv = "RDR-pilot"  # Direct upload works in RDR and RDR-pilot, not in Demo because it is not enabled
print(f"Selected Dataverse installation is <{inp_dv}>")

# Dataverse installation specific info - (URL: result of configuration; DOI: result of user script process + AVU in iRODS with ID 'dv.ds.DOI')
if inp_dv == "RDR":
    BASE_URL = "https://rdr.kuleuven.be"
    dv_ds_DOI = "doi:10.48804/RQLUMN"
elif inp_dv == "Demo":
    BASE_URL = "https://demo.dataverse.org"
    dv_ds_DOI = "doi:10.70122/FK2/GTGRKF"
elif inp_dv == "RDR-pilot":
    BASE_URL = "https://www.rdm.libis.kuleuven.be"
    dv_ds_DOI = "doi:10.82111/JGBUBM"

# Ask the Token for the selected installation
print(
    f"Provide your Token for <{inp_dv}> Dataverse installation. Your Token will be encrypted and saved securely for future reference until expiration."
)
token = maskpass.askpass(prompt="", mask="*")

### Direct upload with requests ###

# create headers with Dataverse token: used in step-1 and step-3
headers_key = {
    "X-Dataverse-key": token,
}
# create headers with content type for data transmission: used in step-2
headers_ct = {
    "Content-Type": "application/x-www-form-urlencoded",
}

# Step-1: GET Direct Upload URL
response1 = requests.get(
    f"{BASE_URL}/api/datasets/:persistentId/uploadurls?persistentId={dv_ds_DOI}&size={df_size}",
    headers=headers_key,
)
# verify status
print(str(response1))  # <Response [200]>
# save the url
url = response1.json()["data"]["url"]

# Step-2: PUT the file in S3
response2 = requests.put(
    url,
    headers=headers_ct,
    data=data,
)
# close the iRODS file
data.close()
# verify status
print(str(response2))  # <Response [200]>

# Step-3: POST (link) the uploaded file to a Dataset
# create a dictionary for the metadata of the data file
dm_dict = {
    "description": "This is the description of the directly uploaded file.",  # TO DO: get from iRODS metadata
    "directoryLabel": "data/subdir1",  # TO DO: get from iRODS, based on the path of the file in a dataset
    "categories": ["Data"],
    "restrict": "false",
    "storageIdentifier": response1.json()["data"]["storageIdentifier"],
    "fileName": src_dataObj.name,
    "mimeType": mimeTypeVal,
    "checksum": {"@type": "SHA-256", "@value": chksumVal},
}
# create a dictionary for jsonData
files = {
    "jsonData": (None, f"{dm_dict}"),
}
# send the POST request
response3 = requests.post(
    f"{BASE_URL}/api/datasets/:persistentId/add?persistentId={dv_ds_DOI}",
    headers=headers_key,
    files=files,
)
# verify status
print(str(response3))  # <Response [200]>

### Clean-up iRODS session ###
session.cleanup()
