"""Direct upload from iRODS to Dataverse S3"""

from typing import Tuple
import requests
from irods.data_object import iRODSDataObject


def get_direct_upload_url(
    base_url: str, dataset_doi: str, datafile_size: int, header_key: dict
) -> Tuple[str, str]:
    """GET request for direct upload to obtain the Dataverse file url and storage ID"""

    api_url = f"{base_url}/api/datasets/:persistentId/"
    upload_url_parameters = (
        f"uploadurls?persistentId={dataset_doi}&size={datafile_size}"
    )

    # request file direct upload
    response = requests.get(
        f"{api_url}{upload_url_parameters}",
        headers=header_key,
        timeout=None,
    )
    if response.status_code != 200:
        raise ConnectionError("Something went wrong", response)

    # get information from response
    data = response.json()["data"]
    file_url = data["url"]
    storage_id = data["storageIdentifier"]

    return file_url, storage_id


def put_in_s3(obj: iRODSDataObject, file_url: str) -> requests.Response:
    """PUT request for direct upload of an iRODS data object on a pre-specified Dataverse URL"""

    # create headers with content type for data transmission: used in step-2
    header_content_type = {
        "Content-Type": "application/x-www-form-urlencoded",
    }  #  content type for data transmission

    # open the iRODS object
    with obj.open("r") as data:
        # PUT the file in S3
        response = requests.put(
            file_url, headers=header_content_type, data=data, timeout=None
        )

    return response


def create_du_md(
    storage_id: str,
    obj_name: str,
    obj_mimetype: str,
    obj_checksum: str,
    obj_directory: str,
) -> dict:
    """Create metadata dictionary for direct upload of an iRODS object"""

    obj_md_dict = {
        "description": "Description of directly uploaded file.",  # TO DO: get from iRODS metadata
        "directoryLabel": obj_directory,
        "categories": ["Data"],
        "restrict": "false",
        "storageIdentifier": storage_id,
        "fileName": obj_name,
        "mimeType": obj_mimetype,
        "checksum": {"@type": "SHA-256", "@value": obj_checksum},
    }

    return obj_md_dict


def post_to_ds(
    obj_md_dict: dict, base_url: str, dataset_doi: str, header_key: dict
) -> requests.Response:
    """POST request for direct upload to return json string"""

    # create a dictionary for jsonData
    files = {
        "jsonData": (None, f"{obj_md_dict}"),
    }
    # send the POST request
    response = requests.post(
        f"{base_url}/api/datasets/:persistentId/add?persistentId={dataset_doi}",
        headers=header_key,
        files=files,
        timeout=None,
    )

    return response
