# based on the investigation on streamUpload
import functions
import maskpass
import json
from irods.data_object import iRODSDataObject


# authenticate in iRODS
session = functions.authenticate_iRODS("~/.irods/irods_environment.json")

# select iRODS object
src = "/set/home/datateam_set/iRODS2DV/iRODSfile2RDR.txt"
src_data_object: iRODSDataObject = session.data_objects.get(src)

# select Dataverse installation
inp_dv = "Demo"
print(f"Selected Dataverse installation is <{inp_dv}>")

# get the base URL and the DOI of a dataset in the selected Dataverse installation
if inp_dv == "RDR":
    BASE_URL = "https://rdr.kuleuven.be/"
    dv_ds_DOI = "doi:10.48804/RQLUMN"
elif inp_dv == "Demo":
    BASE_URL = "https://demo.dataverse.org"
    dv_ds_DOI = "doi:10.70122/FK2/GTGRKF"  # AVU in iRODS with ID 'dv.ds.DOI'
elif inp_dv == "RDR-pilot":
    BASE_URL = "https://www.rdm.libis.kuleuven.be"
    dv_ds_DOI = "doi:10.82111/CQ5E9L"

# Ask the Token for the selected installation
print(
    f"Provide your Token for <{inp_dv}> Dataverse installation. Your Token will be encrypted and saved securely for future reference until expiration."
)
token = maskpass.askpass(prompt="", mask="*")


# authenticate in Dataverse
respond = functions.authenticate_DV(BASE_URL, token)
api = respond[1]


# create the upload URL
url_upload = (
    f"{api.base_url_api_native}/datasets/:persistentId/add?persistentId={dv_ds_DOI}"
)
print(url_upload)

# dictionary with parameters
dict_params = {"size": 147}
print(f"This is the dictionary with parameters ::: {dict_params}")

# dictionary with files
dict_files = {"file": src_data_object.open("r")}

workflow = input(
    "request file upload? type '0' / request addition of file to dataset? type '1'"
)

# dict_data = {
#     "storageIdentifier": "s3://demo-dataverse-org:19205d572bf-99aa2abfd491",
#     "categories": ["Data"],
#     "fileName": "NewlyUploadedFile.txt",
#     "mimeType": "text/plain",
#     "checksum": {"@type": "MD5", "@value": "c5c1518cbbac4c3c952a8eb98198f1d0"},
#     "description": "NewlyUploadedFile description",
# }
# dict_data = {
#     "dataFile": {"filename": "NewlyUploadedFile.txt"}
# }  # tried: dict_data = {filename": "NewlyUploadedFile.txt"} ; dict_data = {"data": {"files": [{"label": "NewlyUploadedFile.txt"}]}}

if workflow == "0":
    # direct upload of a datafile without specifying the data dictionary
    request_directUpload = api.post_request(
        url=url_upload,
        data=None,  # json.dumps({"jsonData": dict_data}),
        files=dict_files,
        auth=True,
        params=None,  # dict_params,
    )
    # close file
    dict_files["file"].close()

    # request_directUpload = api.put_request(
    #     url=url_upload,
    #     auth=True,
    #     params=dict_params,
    # )

    # check the response
    print(request_directUpload.json())
    with open("server-side/uploadedFile.json", "w") as f:
        f.write(request_directUpload.text)

    # Version with POST request:
    # For Demo: OK
    # For RDR-pilot: {'status': 'ERROR', 'message': 'Failed to add file to dataset.'}
    # For RDR: OK

    # Version with PUT request:
    # For Demo: {"status":"ERROR","code":405,"message":"API endpoint does not support this method. Consult our API guide at http://guides.dataverse.org.","requestUrl":"https://demo.dataverse.org/api/v1/datasets/:persistentId/add?persistentId=doi%3A10.70122%2FFK2%2FGTGRKF&User-Agent=pydataverse&key=605344cc-933e-4be2-9fe7-a64802bf4132","requestMethod":"PUT"}
    # For RDR-pilot: {'status': 'ERROR', 'code': 405, 'message': 'API endpoint does not support this method. Consult our API guide at http://guides.dataverse.org.', 'requestUrl': 'https://www.rdm.libis.kuleuven.be/api/v1/datasets/:persistentId/add?persistentId=doi%3A10.82111%2FCQ5E9L&User-Agent=pydataverse&key=9f8db8e5-1fba-425d-8077-472e913e9cf5', 'requestMethod': 'PUT'}
    # For RDR: {'status': 'ERROR', 'code': 405, 'message': 'API endpoint does not support this method. Consult our API guide at http://guides.dataverse.org.', 'requestUrl': 'https://rdr.kuleuven.be/api/v1/datasets/:persistentId/add?persistentId=doi%3A10.48804%2FRQLUMN&User-Agent=pydataverse&key=6b7a80f2-e065-4285-8f9e-90bbc6826855', 'requestMethod': 'PUT'}


elif workflow == "1":

    # modify the metadata of the uploaded file using the data dictionary
    # dictionary with data
    # for Demo:
    dict_data = {
        "storageIdentifier": "s3://demo-dataverse-org:1920bbccc71-50d37c6d6725",
        "categories": ["Data"],
        "fileName": "upload-36",  # "NewlyUploadedFile.txt",
        "mimeType": "text/plain",
        "checksum": {"@type": "MD5", "@value": "c5c1518cbbac4c3c952a8eb98198f1d0"},
        "description": "NewlyUploadedFile description",
    }
    # # for RDR:
    # dict_data = {
    #     "storageIdentifier": "s3://dataverse:19205eefe24-80e78e11258a",
    #     "categories": ["Data"],
    #     "fileName": "NewlyUploadedFile.txt",
    #     "mimeType": "text/plain; charset=US-ASCII",
    #     "checksum": {"@type": "MD5", "@value": "c5c1518cbbac4c3c952a8eb98198f1d0"},
    #     "description": "NewlyUploadedFile description",
    # }
    # can also add a 'directoryLabel'

    request_directUpload = api.post_request(
        url=url_upload,
        data=json.dumps(
            {"jsonData": dict_data}
        ),  # {"jsonData": json.dumps(dict_data)},
        files=dict_files,
        auth=True,
        params=None,
    )
    # Result:
    # <Response [415 Unsupported Media Type]> ==> when the file is None
    # <Response [200 OK]> when the file is specified but no metadata is passed

    # close file
    dict_files["file"].close()

    # request_directUpload = api.put_request(
    #     url=url_upload,
    #     data={"jsonData": json.dumps(dict_data)},
    #     auth=True,
    #     params=None,
    # )
    # # Result: <Response [405 Method Not Allowed]>

    print(request_directUpload)

else:
    print("not a valid input, run again")


# # Try: api.update_datafile_metadata()
# resp = api.update_datafile_metadata(
#     identifier="2384656",
#     json_str="{'filename': 'NewlyUploadedFile.txt'}",
#     is_filepid=True,
# )
# print(
#     resp
# )  # {"status":"ERROR","message":"Error attempting get the requested data file."}
# file URL: https://demo.dataverse.org/file.xhtml?fileId=2384656&version=DRAFT


# Normally we would first create the datafile metadata then upload the file with their metadata
# df = Datafile()
# df.set({'pid': dv_ds_DOI, 'filename': 'NewlyUploadedFile.txt'})
# df.get()
# dict_data = df.json()
# print(f'This is the dictionary with metadata ::: {dict_data}')
