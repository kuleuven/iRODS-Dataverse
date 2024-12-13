import os
import json
import magic
import requests
from irods.session import iRODSSession
from irods.path import iRODSPath
from irods.meta import iRODSMeta, AVUOperation
from irods.column import Criterion
from irods.models import Collection, DataObject, DataObjectMeta
from irods.data_object import iRODSDataObject
from pyDataverse.api import NativeApi
from pyDataverse.models import Datafile
from pyDataverse.utils import read_file
from configparser import ConfigParser
import irods.keywords as kw
import hashlib
from irods2dataverse.avu2json import fill_in_template


# region from_irods
def authenticate_iRODS(env_path):
    """Authenticate to iRODS, in the zone specified in the environment file.

    Parameters
    ----------
    env_path: str
      The filename and location of the JSON specification for the iRODS environment

    Returns
    -------
    session: iRODS session / or False
    """
    if os.path.exists(env_path):
        env_file = os.getenv("iRODS_ENVIRONMENT_FILE", env_path)
        session = iRODSSession(irods_env_file=env_file)
        try:
            with open(env_path) as file:
                data = json.load(file)
                session.collections.get(data["irods_cwd"])
        except:
            print(
                "Invalid authentication please make sure the client is configured correctly"
            )
            return False
        return session
    else:
        print(
            "The environment file does not exist please make sure the client is configured correctly"
        )
        return False


def query_data(atr, val, session):
    """iRODS query to get the data objects destined for publication based on metadata.
    Parameters
    ----------
    atr: str
      the metadata attribute describing the status of publication
    val: str --->> TO DO: CONSIDER LIST OF AV AS INPUT
      the metadata value describing the status of publication, one of 'initiated', 'processed', 'deposited', 'published'
    session: iRODS session

    Returns
    -------
    lobj: list
      list of the data object(s) including iRODS path
    """

    qobj = (
        session.query(Collection.name, DataObject.name)
        .filter(Criterion("=", DataObjectMeta.name, atr))
        .filter(Criterion("=", DataObjectMeta.value, val))
    )
    lobj = set(
        session.data_objects.get(f"{item[Collection.name]}/{item[DataObject.name]}")
        for item in qobj
    )
    return list(lobj)  # qobj


def query_dv(atr, data_objects, installations):
    """iRODS query to get the Dataverse installation for the data that are destined for publication if
    specified as metadata dv.installation

    Parameters
    ----------
    atr: str
      the metadata attribute describing the Dataverse installation
    data_object: irods.DataObject
      Data object to get info from
    installations: list
      List of possible installations
    session: iRODS session

    Returns
    -------
    lMD: list
      list of metadata values for the given attribute
    """
    installations_dict = {k: [] for k in installations}
    installations_dict["missing"] = []
    for item in data_objects:
        md_installations = [
            x.value for x in item.metadata.get_all(atr) if x.value in installations_dict
        ]
        if len(md_installations) == 1:
            installations_dict[md_installations[0]].append(item)
        elif len(md_installations) == 0:
            installations_dict["missing"].append(item)
        # if there are too many installations, the object is ignored

    return {k: v for k, v in installations_dict.items() if len(v) > 0}


def get_object_info(obj):
    """Retrieve object information for direct upload.

    Parameters
    ----------
    obj: iRODSDataObject
      the object meant for publication

    Returns
    -------
    objChecksum: str
      SHA-256 checksum value of iRODS object
    objMimetype: str
      mimetype of iRODS object
    objSize: str
      size of iRODS object
    """

    # Get the checksum value from iRODS
    chksumRes = obj.chksum()
    objChecksum = chksumRes[5:]  # this is algorithm-specific

    # Get the mimetype (from paul, mango portal)
    with obj.open("r") as f:
        blub = f.read(50 * 1024)
        objMimetype = magic.from_buffer(blub, mime=True)

    # Get the size of the object
    objSize = obj.size + 1  # add 1 byte

    return objChecksum, objMimetype, objSize


def save_md(item, atr, val, op):
    """Add metadata in iRODS.

    Parameters
    ----------
    item: str
        Path and name of the data object in iRODS
    atr: str
        Name of metadata attribute
    val: str
        Value of metadata attribute
    session: iRODS session
    op: str
        Metadata operation, one of "add" or "set".
    """

    try:
        if op == "add":
            item.metadata.add(str(atr), str(val))
            print(
                f"Metadata attribute {atr} with value {val}> is added to data object {item}."
            )
            return True
        elif op == "set":
            item.metadata.set(f"{atr}", f"{val}")
            print(f"Metadata attribute {atr} is set to <{val}> for data object {item}.")
            return True
        else:
            print(
                "No valid metadata operation is selected. Specify one of 'add' or 'set'."
            )
            return True
    except Exception as e:  # change this to specific exception
        print(type(e))
        print(f"An error occurred: {e}")
        return False


# this one could go to avu2json
def get_template(path_to_template, metadata):
    """Turn a metadata dictionary into a .

    Parameters
    ----------
    path_to_template : str
        The path to the original template
    metadata : dict
        A simplified dictionary with metadata

    Returns
    -------
    template: dict
        A complete template as dictionary
    """
    with open(path_to_template) as f:
        template = json.load(f)
    # fill in template
    fill_in_template(template, metadata)
    return template


# endregion
# region todv
def authenticate_DV(url, tk):
    """Check that the use can be authenticated to Dataverse.

    Parameters
    ----------
    url: str
        The URL to the Dataverse installation
    tk: str
        The Dataverse API Token

    Returns
    -------
    status: str
        The HTTP status for accessing the Dataverse installation.
    api: list
        Status and pyDataverse object
    """

    api = NativeApi(url, tk)
    resp = api.get_info_version()
    status = resp.status_code

    return status, api


def instantiate_selected_class(installationName, config):
    """Instantiate Dataset class based on the selected Dataverse installation.

    Parameters
    ----------
     installationName: str
        The Dataverse installation specified by the user
    config: ini
        The file to initialize the configured Dataset classes

    Returns
    -------
     selectedClass: class
        The class to instantiate
    """

    config_section = config[installationName]
    modulename, classname = config_section["className"].split(".", 2)
    importlib = __import__("importlib")
    module = importlib.import_module(f"irods2dataverse.{modulename}")
    selectedClass = getattr(module, classname)

    return selectedClass()


def setup(inp_dv, inp_tk):
    """Establish a session for the selected Dataverse installation and create an empty dataset.

     Parameters
     ----------
     inp_dv: str
        The target Dataverse installation
     inp_tk: str
        The user token

    Returns
    -------
    msg: str
        The message depends on the HTTP status for accessing the Dataverse installation.
        If the HTTP status is 200, then the process can continue and the user gets the path to metadata template they need to fill in for the selected Dataverse installation.
        If the HTTP status is not 200, the process cannot continue until the user can provide valid authentication credentials.
    resp: list
        The returns of authenticate_DV
    ds: class
        The class that is instantiated
    """

    # read once the configuration file located in a hard-coded path
    config = ConfigParser()
    config.read("src/irods2dataverse/customization.ini")
    # Check that the Dataverse installation is configured
    if inp_dv in config.sections():
        print("The selected Dataverse installation is configured")
        # Instantiate the Dataset class of the selected Dataverse installation
        ds = instantiate_selected_class(inp_dv, config)
        # Gen information of the instantiated class
        BASE_URL = ds.baseURL
        mdPath = ds.metadata_template
        # Authenticate to Dataverse installation
        status, api = authenticate_DV(BASE_URL, inp_tk)
        if status == 200:
            # If the user is authenticated, direct to the minimum metadata of the selected Dataverse installation
            msg = f"Minimum metadata should be provided to proceed with the publication.\nThe metadata template can be found in {mdPath}."
        else:
            msg = "The authentication to the selected Dataverse installation failed."
    else:
        msg = "The Dataverse installation you selected is not configured."
        ds = None
    print(msg)
    return api, ds


def validate_md(ds, md):
    """Validate that the metadata template is up-to-date

    Parameters
    ----------
    ds : Dataverse Dataset
        The initial Dataset object of the selected Dataverse installation
    md : str
        The path to the json metadata template, filled in or not

    Returns
    -------
    resp : bool
        It is `True` if the metadata template fits the Dataverse expectations and `False` if it does not.
    """
    if isinstance(md, str):
        md = read_file(md)
    elif isinstance(md, dict):
        md = json.dumps(md)
    try:
        ds.from_json(md)
        resp = (
            ds.validate_json()
        )  # filename_schema = path to schema + ; with and without hidden class attributes
        return resp
    except Exception as e:  # change this to specific exception
        print(type(e))
        print(f"An error occurred: {e}")
        return False


def deposit_ds(api, inp_dv, ds):
    """Create a Dataverse dataset with user specified metadata

    Parameters
    ----------
    api : list
        Status and pyDataverse object
    inp_dv: str
        The selected Dataverse installation

    Returns
    -------
    dsStatus : bool
        Upload status
    dsPID : str
        Dataset Persistent Identifier
    dsID : str
        Dataverse Identifier
    dsPURL : str
        Dataset Private URL
    """

    resp = api.create_dataset(inp_dv.lower(), ds.json()).json()
    dsStatus = resp["status"]
    dsPID = resp["data"]["persistentId"]
    dsID = resp["data"]["id"]
    # resp = api.create_dataset_private_url(dsPID) # RDR does not allow PURL creation; move to Class definition?
    # dsPURL = resp.json()["data"]["link"]

    return (
        dsStatus,
        dsPID,
        dsID,
    )  # dsPURL


def save_df(data_object, trg_path, session):
    """Save locally the iRODS data objects destined for publication

    Parameters
    ----------
    objPath: str
      iRODS path of a data object destined for publication
    objName: str
      Filename of a data object destined for publication
    trg_path: str
      Local directory to save data
    session: iRODS session
    """
    opts = {kw.FORCE_FLAG_KW: True}
    # TO DO: checksum in case download is not needed?
    """
    def checksum(f):
        md5 = hashlib.md5()    
        md5.update(open(f).read())
        return md5.hexdigest()

    def is_contents_same(f1, f2):
        return checksum(f1) == checksum(f2)
    """
    session.data_objects.get(data_object.path, f"{trg_path}/{data_object.name}", **opts)


def deposit_df(api, dsPID, data_object_name, inp_path):
    """Upload the list of data files in Dataverse Dataset

    Parameters
    ----------
    api : list
        Status and pyDataverse object
    dsPID : str
        Dataset Persistent Identifier
    inp_df : str
        The name of the file destined for publication
    inp_path: str
        The path to the local directory to save the data files

    Returns
    -------
    dfResp: list
        API response from each data file upload
    dfPID: list
        String in JSON format with persistent ID and filename.
    """

    df = Datafile()
    df.set({"pid": dsPID, "filename": data_object_name})
    df.get()
    resp = api.upload_datafile(dsPID, f"{inp_path}/{data_object_name}", df.json())
    # if resp.status_code != 200: # deal with errors?
    #     return resp

    print(f"{data_object_name} is uploaded")

    return resp.json()  # , df.json()


# endregion

# region directupload


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
        header=header_key,
        files=files,
    )
    # # verify status
    # print(str(response3))  # <Response [200]> ==> for user script

    return response


# endregion


def extract_atr(JSONstr, atr):
    """Extract attribute value from the datafile JSON response, for a given datafile.

    Parameters
    ----------
    JSONstr : str
        A string including a JSON structure with metadata
    atr : str
        The attribute to extract from the dictionary

    Returns
    -------
    lst_val: list
        Metadata value as a string item for each file uploaded in Dataverse
    """

    JSONstr.replace("False", '"False"')
    json_obj = json.dumps(JSONstr)
    val = json_obj[atr]  # integers

    return val
