import os
import json
from irods.session import iRODSSession
from irods.meta import iRODSMeta, AVUOperation
from irods.column import Criterion
from irods.models import Collection, DataObject, DataObjectMeta
from pyDataverse.api import NativeApi
from pyDataverse.models import (
    Dataset,
    Datafile,
)  # import also the DVObject to change class attributes?
from pyDataverse.utils import read_file
import irods.keywords as kw


def authenticate_iRODS(env_path):
    """Authenticate to iRODS, in the zone specified in the environment file.

    Parameters
    ----------
    env_path: str
      The filename and location of the JSON specification for the iRODS environment

    Returns
    -------
    session: iRODS session
    """
    if os.path.exists(env_path):
        env_file = os.getenv("iRODS_ENVIRONMENT_FILE", env_path)
        session = iRODSSession(irods_env_file=env_file)
        return session
    else:
        print("the environment file does not exist")
        return None
        


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
    val: str --->> CONSIDER LIST OF AV AS INPUT
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
        lobj.append(f"{item[Collection.name]}/{item[DataObject.name]}")
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


def query_dv(atr, objPath, objName, session):
    """iRODS query to get the Dataverse installation the data are destined for publication.

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
    for item in range(len(objPath)):
        qMD = (
            session.query(
                Collection.name,
                DataObject.name,
                DataObjectMeta.name,
                DataObjectMeta.value,
            )
            .filter(Criterion("=", Collection.name, objPath[item]))
            .filter(Criterion("=", DataObject.name, objName[item]))
            .filter(Criterion("=", DataObjectMeta.name, atr))
        )
        for item in qMD:
            lMD.append(f"{item[DataObjectMeta.value]}")

    return lMD


def get_template(inp_dv):
    """Direct user to metadata template.

    Parameters
    ----------
    inp_dv: str
        The selected Dataverse installation

    Returns
    -------
    msg : str
        A message including the path to the JSON file with the required metadata template for the selected Dataverse installation
    mdPath : str
        The path to the metadata template for the selected Dataverse installation
    """

    if inp_dv == "RDR":
        mdPath = "doc/metadata/template_RDR.json"
    elif inp_dv == "Demo":
        mdPath = "doc/metadata/template_Demo.json"

    msg = f"Minimum metadata should be provided to proceed with the publication.\nPlease fill in the metadata template {mdPath}, save and hit enter to continue."

    return print(msg), mdPath


def setup(inp_dv, inp_tk):
    """Establish a session for the selected Dataverse installation.

     Parameters
     ----------
     inp_dv: str
        The target Dataverse installation

    Returns
    -------
    msg: str
        The message depends on the HTTP status for accessing the Dataverse installation.
        If the HTTP status is 200, then the process can continue and the user gets the path to metadata template they need to fill in for the selected Dataverse installation.
        If the HTTP status is not 200, the process cannot continue until the user can provide valid authentication credentials.
    resp : ...
        ...
    """
    if inp_dv == "RDR":
        BASE_URL = "https://rdr.kuleuven.be/"
    elif inp_dv == "Demo":
        BASE_URL = "https://demo.dataverse.org"
    else:
        print("The Dataverse installation you selected is not configured.")

    resp = authenticate_DV(BASE_URL, inp_tk)
    if resp[0] == 200:
        msg = get_template(inp_dv)
    else:
        msg = "The authentication to the selected Dataverse installation failed."

    return msg, resp


def initiate_ds(inp_dv):
    """Based on the Dataverse installation, initiate the Dataset

    Parameters
    ----------
    inp_dv: str
        The selected Dataverse installation

    Returns
    -------
    ds : Dataverse Dataset
        The initial Dataset object of the selected Dataverse installation
    """
    if inp_dv == "RDR":
        ds = Dataset()  # RDRDataset()
    elif inp_dv == "Demo":
        ds = Dataset()

    return ds


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

    ds.from_json(read_file(md))
    resp = ds.validate_json()

    return resp


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


def save_df(objPath, objName, trg_path, session):
    """Save locally the iRODS data objects destined for publication
    Parameters
    ----------
    objPath: list
      iRODS path of each data object for publication
    objName: list
      Filename of each data object for publication
    trg_path: str
      Local directory to save data
    session: iRODS session
    """
    opts = {kw.FORCE_FLAG_KW: True}

    for item in range(len(objName)):
        # chksum(f"{objPath[item]}/{objName[item]}", f"{trg_path}/{objName[item]}")
        session.data_objects.get(
            f"{objPath[item]}/{objName[item]}",
            f"{trg_path}/{objName[item]}",
            **opts,
        )


def deposit_df(api, dsPID, inp_df, inp_path):
    """Upload the list of data files in Dataverse Dataset
    Parameters
    ----------
    api : list
        Status and pyDataverse object
    dsPID : str
        Dataset Persistent Identifier
    inp_df : list
        The name of the files for publication
    inp_path: str
        The path to the local directory to save the data files

    Returns
    -------
    dfResp: list
        API response from each data file upload
    dfPID: list
        String in JSON format with persistent ID  and filename.
    """

    dfResp = []
    dfPID = []
    for inp_i in inp_df:
        df = Datafile()
        df.set({"pid": dsPID, "filename": inp_i})
        df.get()
        resp = api.upload_datafile(dsPID, f"{inp_path}/{inp_i}", df.json())

        print(f"{inp_i} is uploaded")

        dfResp.append(resp.json())
        dfPID.append(df.json())

    return dfResp, dfPID


def extract_atr(JSONstr, atr):
    """Extract attribute value from the datafile JSON response, for a given list of datafiles
    Parameters
    ----------
    JSONstr : str
        A string including a JSON structure for the persistent identified and the filename
    atr : str
        The attribute to extract from teh dictionary

    Returns
    -------
    lst_val: list
        Metadata value as a string item for each file uploaded in Dataverse
    """

    lst_val = []
    # TO DO: apply for JSONstr in list_of_JSONstr
    json_obj = json.loads(JSONstr)
    val = json_obj[atr]
    lst_val.append(val)

    return lst_val


def save_md(item, atr, val, session):
    """Add metadata in iRODS
    Parameters
    ----------
    item: str
        Path and name of the data object in iRODS
    atr: str
        Name of metadata attribute
    val: str
        Value of metadata attribute
    session: iRODS session
    """

    obj = session.data_objects.get(f"{item}")
    obj.metadata.apply_atomic_operations(
        AVUOperation(operation="add", avu=iRODSMeta(f"{atr}", f"{val}"))
    )
