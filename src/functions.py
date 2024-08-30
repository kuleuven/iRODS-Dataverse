import os
import json
from irods.session import iRODSSession
from irods.path import iRODSPath
from irods.meta import iRODSMeta, AVUOperation
from irods.column import Criterion
from irods.models import Collection, DataObject, DataObjectMeta
from pyDataverse.api import NativeApi
from pyDataverse.models import Datafile
from pyDataverse.utils import read_file
from configparser import ConfigParser
import irods.keywords as kw
import hashlib



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
            print("Invalid authentication please make sure the client is configured correctly")
            return False
        return session
    else:
        print("The environment file does not exist please make sure the client if configured correctly")
        return False
        


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

    lobj = []
    qobj = (
        session.query(Collection.name, DataObject.name, DataObjectMeta.name)
        .filter(Criterion("=", DataObjectMeta.name, atr))
        .filter(Criterion("=", DataObjectMeta.value, val))
    )
    for item in qobj:
        #lobj.append(f"{item[Collection.name]}/{item[DataObject.name]}")
        obj_location = f"{item[Collection.name]}/{item[DataObject.name]}"
        obj = session.data_objects.get(obj_location)
        lobj.append(obj)
    lobj = list(set(lobj))
    return lobj  # qobj


def split_obj(obj):
    """Split input in path and filename.

    Parameters
    ----------
    obj: list
      iRODS path and name of object(s) for publication

    Returns
    -------
    objPath: list
      iRODS path of each data object for publication
    objName: list
      Filename of each data object for publication
    """

    objPath = []
    objName = []
    for item in obj:
        res = item.split("/")
        obji = res[len(res) - 1]
        objPath.append(item[: -(len(obji) + 1)])
        objName.append(obji)

    return objPath, objName


def check_identical_list_elements(list):
    """check if all elements in a list are identical
    param: list
    returns: bool"""
    return all(i == list[0] for i in list)

def query_dv(atr, data_object, session):
    """iRODS query to get the Dataverse installation for the data that are destined for publication if
    specified as metadata dv.installation

    Parameters
    ----------
    atr: str
      the metadata attribute describing the Dataverse installation
    objPath: list
      iRODS path of each data object for publication
    objName: list
      Filename of each data object for publication
    session: iRODS session

    Returns
    -------
    lMD: list
      list of metadata values for the given attribute
    """

    lMD = []
    for item in range(len(data_object)):
        qMD = (
            session.query(
                Collection.name,
                DataObject.name,
                DataObjectMeta.name,
                DataObjectMeta.value,
            )
            .filter(Criterion("=", Collection.name, data_object[item].path))
            .filter(Criterion("=", DataObject.name, data_object[item].name))
            .filter(Criterion("=", DataObjectMeta.name, atr))
        )
        for item in qMD:
            lMD.append(f"{item[DataObjectMeta.value]}")

    if check_identical_list_elements(lMD):
        return lMD
    else: 
        print("Multiple dataverse installations found in metadata ")
        return []


def get_data_object(session, object_location):
    """do operations on the data_object
    param: session, object path 
    returns: obj
    
    """
    #if not session.collections.exists(object_name):
     #   object_location = iRODSPath('ghum', 'home/datateam_ghum',
      #                              'irods_to_dataverse', object_name)
    print(object_location)
    obj = session.data_objects.get(object_location)
    print(obj.name)
    print(obj.collection)
    print(obj.path)
    return obj






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
    module = __import__(modulename)
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
    config.read("customization.ini")
    print(config.sections)
    # Check that the Dataverse installation installation is configured
    if inp_dv in config.sections():
        print("true")
        # Instantiate the Dataset class of the selected Dataverse installation
        ds = instantiate_selected_class(inp_dv, config)
        # Gen information of the instantiated class
        BASE_URL = ds.baseURL
        mdPath = ds.metadataTemplate
        # Authenticate to Dataverse installation
        resp = authenticate_DV(BASE_URL, inp_tk)
        if resp[0] == 200:
            # If the user is authenticated, direct to the minimum metadata of the selected Dataverse installation
            msg = f"Minimum metadata should be provided to proceed with the publication.\nPlease fill in the metadata template {mdPath}."
        else:
            msg = "The authentication to the selected Dataverse installation failed."
    else:
        msg = "The Dataverse installation you selected is not configured."
        resp = None
        ds = None

    return print(msg), resp, ds


def validate_md(ds, md):
    """Validate that the metadata template is up-to-date [NOTE: In its current state this function is not needed]

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
    try:
        ds.from_json(read_file(md))
        resp = ds.validate_json()
        return resp
    except Exception as e: #change this to specific exception
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

    resp = api.create_dataset(inp_dv.lower(), ds.json())
    dsStatus = resp.json()["status"]
    dsPID = resp.json()["data"]["persistentId"]
    dsID = resp.json()["data"]["id"]
    resp = api.create_dataset_private_url(dsPID)
    dsPURL = resp.json()["data"]["link"]

    return dsStatus, dsPID, dsID, dsPURL

def checksum(f):
    md5 = hashlib.md5()    
    md5.update(open(f).read())
    return md5.hexdigest()

def is_contents_same(f1, f2):
    return checksum(f1) == checksum(f2)



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

    print(f"{data_object_name} is uploaded")

    return resp.json()  # , df.json()


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

   # obj = session.data_objects.get(f"{item}")
    try:
        if op == "add":
            item.metadata.apply_atomic_operations(
                AVUOperation(operation="add", avu=iRODSMeta(f"{atr}", f"{val}"))
            )
            print(
                f"Metadata attribute {atr} with value {val}> is added to data object {item}."
            )
            return True
        elif op == "set":
            item.metadata.set(f"{atr}", f"{val}")
            print(f"Metadata attribute {atr} is set to <{val}> for data object {item}.")
            return True
        else:
            print("No valid metadata operation is selected. Specify one of 'add' or 'set'.")
            return True
    except Exception as e: #change this to specific exception
        print(type(e))
        print(f"An error occurred: {e}")
        return False
    

