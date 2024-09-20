# Investigation of the server-to-server download/upload workflow

This document goes over the possibilities we found for implementing the workflow iRODS-to-Dataverse on the server side. 

We are testing on the following installations: Demo installation; RDR installation; RDR Pilot installation. 

We have been discussing the iRODS-Dataverse integration with SURF, and they can test on the DANS installation, however, as far as we know, from SURF's side no action has been taken on that respect yet.

## Motivation
In the user script, the data is downloaded from iRODS locally, and then uploaded to Dataverse. Instead, we envision the user would not need to download the data locally. 
The user would be able to delegate the copy of the data from iRODS to Dataverse, in the iRODS and Dataverse servers.

## Requirements
We aim to a server-side implementation that is not product-specific (e.g. ManGO only) and that can be reused by the iRODS community. This is also the requirement from SURF. SURF would like to have a low-level solution and be able to plug it in the systems they control.

We assume we cannot have an admin account to every Dataverse installation we target. It could be possible to have an admin account for KU Leuven RDR. SURF could look into requesting an admin account for DANS.


## Direct Upload to Dataverse in S3

Direct upload is supported in Dataverse installations via the <a href="https://guides.dataverse.org/en/latest/developers/s3-direct-upload-api.html">Direct DataFile Upload/Replace API</a>. This is a two step process: (1) Request a direct upload of a file (2) Add the uploaded file to the dataset.

Several Dataverse clients exist to interact with Dataverse see <a href="https://guides.dataverse.org/en/latest/api/client-libraries.html">Dataverse documentation</a>. You may also refer to [the latest internal overview of Dataverse clients](../../overview_DataverseClients.md).

According to Dataverse documentation, DVUploader supports direct upload. Other tools may support direct upload, such as the ones we list in this document. 

> Note that a Dataverse installation may not be configured to use S3 storage with direct upload enabled. Therefore, we need to investigate Dataverse installations case-by-case and whitelist the installations we could support.

### CURL

* Works for RDR pilot installation.

Command to request a direct upload:
```
$ curl -H "X-Dataverse-key:XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" "https://www.rdm.libis.kuleuven.be/api/datasets/:persistentId/uploadurls?persistentId=doi:10.82111/CQ5E9L&size=1024"
```
Result:
```
{"status":"OK","data":{"url":"https://rdmo.icts.kuleuven.be/dataverse-pilot/10.82111/CQ5E9L/191ec29afaa-4d46fed9d6ae?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240913T161400Z&X-Amz-SignedHeaders=host&X-Amz-Expires=3600&X-Amz-Credential=aihee9mieQueigeisoop%2F20240913%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=b466a0479b69f7efe4d57029e2a6b8d9ee7b3e2fe3f504222a7f61c4731eaadc","partSize":1073741824,"storageIdentifier":"s3://dataverse-pilot:191ec29afaa-4d46fed9d6ae"}}
```

*TO DO-1: Check the 'expires' info. Is this calibrated according to the requested size? Can the time be increased?*

*TO DO-2: Follow-up with checking the command to add the uploaded file in the dataset.*

* Does not work for Demo installation. 

Command:
```
$ curl -H "X-Dataverse-key:XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" "https://demo.dataverse.org/api/datasets/:persistentId/uploadurls?persistentId=doi:10.70122/FK2/GTGRKF&size=1024"
```
Result: 
`{"status":"ERROR","message":"Direct upload not supported for files in this dataset: 2362111"}`

Tested also with a published version `doi:10.70122/FK2/DJ6YQF` and the result was the same.

* Does not work for RDR installation. 

Command:
```
$ curl -H "X-Dataverse-key:XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" "https://www.rdm.libis.kuleuven.be/api/datasets/:persistentId/uploadurls?persistentId=doi:10.48804/RQLUMN&size=1024"
```
Result: 
`{"status":"ERROR","message":"Bad API key"}`

### pyDataverse

Supported by the Global Dataverse Community Consortium (GDCC).

Reference: https://github.com/gdcc/pyDataverse

The curl commands are wrapped in the python module pyDataverse. For the latest internal script see [directUpload.py](../directUpload.py).


```
src_data_object: iRODSDataObject = session.data_objects.get(src)
dict_files = {"file": src_data_object.open("r")}

request_directUpload = api.post_request(
    url=url_upload,   # URL including the Dataset DOI
    data=None,        # no dict_data
    files=dict_files, # direct reading from iRODS
    auth=True,        # token is sent to DV
    params=None,      # no dict_params,
)
```
* Does not work for RDR pilot installation.

Result: `{'status': 'ERROR', 'message': 'Failed to add file to dataset.'}`

* Works for Demo installation.
* Works for RDR installation.

However:

> The result is a file uploaded directly from iRODS without download, linked already to the dataset with the specified DOI but the filename is specified as upload-#. The mimetype is correctly detected. A Following POST request to modify the jsonData is not working (see latest internal  python script)
> Only a POST request works and the post request does not work without the file parameter. If there is no file parameter the result is `<Response [415 Unsupported Media Type]>`. For the PUT request the result is `<Response [405 Method Not Allowed]>`.


Result of a working case (example):
```
{
    "status": "OK",
    "message": {
        "message": "This file has the same content as upload that is in the dataset. "
    },
    "data": {
        "files": [
            {
                "description": "",
                "label": "upload-12",
                "restricted": false,
                "version": 1,
                "datasetVersionId": 259491,
                "dataFile": {
                    "id": 2383334,
                    "persistentId": "",
                    "filename": "upload-12",
                    "contentType": "text/plain; charset=US-ASCII",
                    "friendlyType": "Plain Text",
                    "filesize": 147,
                    "description": "",
                    "storageIdentifier": "s3://demo-dataverse-org:19204d5297f-15c0c8a8e905",
                    "rootDataFileId": -1,
                    "md5": "c5c1518cbbac4c3c952a8eb98198f1d0",
                    "checksum": {
                        "type": "MD5",
                        "value": "c5c1518cbbac4c3c952a8eb98198f1d0"
                    },
                    "tabularData": false,
                    "creationDate": "2024-09-18",
                    "fileAccessRequest": false
                }
            }
        ]
    }
}
```

*TO DO-3: Try to pass the filename upon opening the file from iRODS. Continue the investigation for the two-step process in pyDataverse. Also try renaming datafile after upload using api.update_datafile_metadata().*

*TO DO-4: Investigate the synchronous and asynchronous requests supported in pyDataverse, see `_sync_request` and `_async_request` of class `Api`.*


### Java dvuploader

Supported by the Global Dataverse Community Consortium (GDCC).

Reference: https://github.com/GlobalDataverseCommunityConsortium/dataverse-uploader. 

The Java DVUploader can be used to upload files from a specified directory into a specified Dataset. According to the documentation, Java DVUploader can be useful in a number of cases compared to the web interface:
- there are hundreds or thousands of files to upload,
- when automatic verification of error-free and complete upload of files is desired,
- when new files are being generated/added to a directory and Dataverse needs to be updated with just the new files,
- uploading of files needs to be automated, e.g. added to an instrument or analysis script or program.

For RDR, there is a fix for Java DVUploader with GO client. 

Does the Java dvuploader support tagging?

*TO DO-5: Investigate direct upload with the Java DVUploader.*


### Python-dvuploader

Supported by the Global Dataverse Community Consortium (GDCC).

Reference: https://github.com/gdcc/python-dvuploader.

```
import dvuploader as dv

DV_URL = "https://demo.dataverse.org"
API_TOKEN = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
PID = "doi:10.70122/FK2/K7KGHG"

files = [
    *dv.add_directory("./dirL1"),  # Add an entire directory
]

dvuploader = dv.DVUploader(files=files)
dvuploader.upload(
    api_token=API_TOKEN,
    dataverse_url=DV_URL,
    persistent_id=PID,
    n_parallel_uploads=3,  # Whatever your instance can handle
)
```

* Does not work for Demo installation.
Result: `Direct upload not supported. Falling back to Native API.` but the files are uploaded.

* Does not work for RDR pilot and RDR installations.
Result: `ClientResponseError(aiohttp.client_exceptions.ClientResponseError: 501, message='Not Implemented', url=URL('https://rdmo.icts.kuleuven.be/dataverse-pilot/10.82111/CQ5E9L/1920e82e122-8cf97cba6b31?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240920T081831Z&X-Amz-SignedHeaders=host&X-Amz-Expires=3600&X-Amz-Credential=aihee9mieQueigeisoop/20240920/us-east-1/s3/aws4_request&X-Amz-Signature=5d662f12a0565b38e2c4392ef90d60816e2482dabfa563d85fce34e0cfa9b18e')`


* Python-dvuploader does not support <a href="https://guides.dataverse.org/en/latest/api/native-api.html#request-signed-url">URL signing</a>. For RDR, tagging is not supported while the dvuploader python module assumes that tagging is supported. We do not know whether Demo and DANS support tagging, but since it is not a solution for RDR, investigating for other installations does not seem to be a priority.

* Python-dvuploader is not a viable option for direct upload and a lot of work should be done to make it a viable option. Additional work needed to make python dvuploader viable option: We can make a PR to the python-dvuploader to add an option for not supported tagging, like Eryk did in other cases. However, multipart uploads for large files were still a problem, so we will need to investigate how to solve this issue with another PR. In Eryk's golang code he used an S3 library for a direct access to s3 using the s3 protocol for multipart uploads.



### Javascript client

Supported by the Institute for Quantitative Social Science (IQSS).

The Javascript client is currently under development. In the documentation it is mentioned that the client supports direct upload but this remains to be tested for each installation. Reference: https://github.com/IQSS/dataverse-client-javascript and specifically for the direct upload, see the *File Uploading Use Cases* at https://github.com/IQSS/dataverse-client-javascript/blob/develop/docs/useCases.md#file-uploading-use-cases

A stable 1.x version of this package can be installed with warnings and 7 vulnerabilities (5 moderate, 2 high). An unstable 2.x version of this package can be installed with 5 vulnerabilities (3 moderate, 2 high).

* For authentication, apart from the API Token, there is a session cookie option. The session cookie is an experimental feature and a mechanism should be enabled in the Dataverse installation.

*TO DO-6: Discuss whether we should already investigate the Javascript client and if so, continue with the investigation.*

## ManGO-specific implementation

Using ManGO Flow we can provide a seamless integration of iRODS-Dataverse to the ManGO user.

ManGO flow could be installed independently of ManGO in an iRODS vanilla container and potentially provide a solution for SURF (to be discussed). SURF is already investigating ManGO flow.


## Dataverse User Token and Session duration

The user Token is currently asked once by the user, in an interactive user script. The Token is not saved neither locally nor in iRODS.

We need to check whether, policy-wise, is acceptable to encrypt and save the Dataverse token.

For the iRODS session, the process followed in ManGO Flow could be used. This means that an operator account renews the session to keep the connection active until the requested process finishes. 

*TO DO-7: If a process is followed asynchronously, investigate how we can use the Dataverse token.*


## Admin account for Dataverse

Is the Dataverse admin account necessary to keep the Dataverse session active and implement the integration with ManGO Flow?

What is the procedure to request an admin account for RDR?


## Other potential investigation

- Globus transfer
- Other Dataverse clients
