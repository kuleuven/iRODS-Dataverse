import requests


def create_headers(token):
    """Create information to pass on the header for direct upload

    Parameters
    ----------
    token: str
      the Dataverse token given by the user

    Returns
    -------
    header_key: dict
      the token used in direct upload step-1 and step-3
    header_ct: dict
      the content type for data transmission used in direct upload step-2
    """

    # create headers with Dataverse token: used in step-1 and step-3
    header_key = {
        "X-Dataverse-key": token,
    }
    # create headers with content type for data transmission: used in step-2
    header_ct = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    return header_key, header_ct


def get_du_url(BASE_URL, dv_ds_DOI, df_size, header_key):
    """GET request for direct upload

    Parameters
    ----------
    BASE_URL: str
      class attribute baseURL
    dv_ds_DOI: str
      Dataset Persistent Identifier
    objSize: str
      size of iRODS object
    header_key: dict
      the token used in direct upload

    Returns
    -------
    response1: json
      json response of GET request for direct upload
    fileURL: str
      Dataverse URL for the iRODS object meant for publication
    strorageID: str
      Dataverse storage identified
    """

    # request file direct upload
    response = requests.get(
        f"{BASE_URL}/api/datasets/:persistentId/uploadurls?persistentId={dv_ds_DOI}&size={df_size}",
        headers=header_key,
    )
    # # verify status
    # print(str(response1))  # <Response [200]> ==> for user script
    if response.status_code != 200:
        raise ConnectionError("Something went wrong", response)
    # save the url
    data = response.json()["data"]
    fileURL = data["url"]
    strorageID = data["storageIdentifier"]

    return fileURL, strorageID


def put_in_s3(obj, fileURL, headers_ct):
    """PUT request for direct upload

    Parameters
    ----------
    obj: iRODSDataObject
      the object meant for publication
    fileURL: str
      Dataverse URL for the iRODS object meant for publication
    headers_ct: dict
      the content type for data transmission used in direct upload step-2

    Returns
    -------
    response2: json
      json response of PUT request for direct upload
    """

    # open the iRODS object
    with obj.open("r") as data:
        # PUT the file in S3
        response = requests.put(
            fileURL,
            headers=headers_ct,
            data=data,
        )
    # # verify status
    # print(str(response2))  # <Response [200]>  ==> for user script

    return response


def create_du_md(storageID, objName, objMimetype, objChecksum):
    """Create direct upload metadata dictionary

    Parameters
    ----------
    response1: json
      json response of GET request for direct upload
    objName: str
      the name of the object to be stored
    objMimetype: str
      mimetype of iRODS object
    objSize: str
      size of iRODS object

    Returns
    -------
    obj_md_dict: dict
      the metadata dictionary for the file meant for publication
    """

    obj_md_dict = {
        "description": "This is the description of the directly uploaded file.",  # TO DO: get from iRODS metadata
        "directoryLabel": "data/subdir1",  # TO DO: get from iRODS, based on the path of the file in a dataset
        "categories": ["Data"],
        "restrict": "false",
        "storageIdentifier": storageID,
        "fileName": objName,
        "mimeType": objMimetype,
        "checksum": {"@type": "SHA-256", "@value": objChecksum},
    }

    return obj_md_dict


def post_to_ds(obj_md_dict, BASE_URL, dv_ds_DOI, header_key):
    """POST request for direct upload

    Parameters
    ----------
    obj_md_dict: dict
      the metadata dictionary for the file meant for publication
    BASE_URL: str
      class attribute baseURL
    dv_ds_DOI: str
      Dataset Persistent Identifier
    header_key: dict
      the token used in direct upload

    Returns
    -------
    response3:  json
      json response of POST request for direct upload
    """

    # create a dictionary for jsonData
    files = {
        "jsonData": (None, f"{obj_md_dict}"),
    }
    # send the POST request
    response = requests.post(
        f"{BASE_URL}/api/datasets/:persistentId/add?persistentId={dv_ds_DOI}",
        headers=header_key,
        files=files,
    )
    # # verify status
    # print(str(response3))  # <Response [200]> ==> for user script

    return response
