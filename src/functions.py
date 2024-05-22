import os
import json
from irods.session import iRODSSession
from irods.meta import iRODSMeta, AVUOperation
from irods.column import Criterion
from irods.models import Collection, DataObject, DataObjectMeta
from pyDataverse.api import NativeApi
from pyDataverse.models import Dataset
from pyDataverse.utils import read_file


def authenticate_iRODS(env_path):
    """...

    Parameters
    ----------
    env_path: str
      The filename and location of the JSON specification for the iRODS environment

    Returns
    -------
    session
      iRODS session
    """
    env_file = os.getenv("iRODS_ENVIRONMENT_FILE", os.path.expanduser(env_path))
    session = iRODSSession(irods_env_file=env_file)
    return session


def authenticate_DV(url, tk):
    """Check that the use can be authenticated to Dataverse
    Parameters
    ----------
    url: str
        The URL to the Dataverse installation
    tk: str
        The Dataverse API Token

    Returns
    -------
    status : str
        The HTTP status for accessing the Dataverse installation.
    """
    api = NativeApi(url, tk)
    resp = api.get_info_version()
    status = resp.status_code

    return status, api


def query_data(atr, val, session):
    """...

    Parameters
    ----------
    atr: str
      the metadata attribute describing the status of publication
    val: str --->> CONSIDER LIST OF AV AS INPUT
      the metadata value describing the status of publication, one of 'initiated', 'processed', 'deposited', 'published'
    session: iRODS session

    Returns
    -------
    lobj
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
    return lobj  # qobj  # maybe remove qobj


def query_dv(atr, obj, session):
    """...

    Parameters
    ----------
    atr: str
      the metadata attribute describing the Dataverse installation
    obj: list
      iRODS path and name of object(s) for publication
    session: iRODS session

    Returns
    -------
    lMD
      list of metadata values for the given attribute
    """

    objPath = []
    objName = []
    for item in obj:
        res = item.split("/")
        obji = res[len(res) - 1]
        objPath.append(item[: -(len(obji) + 1)])
        objName.append(obji)

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
    """Directs user to metadata template.

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
        mdPath = "doc/metadata/md_RDR.json"
    elif inp_dv == "Demo":
        mdPath = "doc/metadata/md_Demo.json"

    msg = f"Minimum metadata should be provided to proceed with the publication.\nPlease fill in the metadata template {mdPath}, save and hit enter to continue."

    return print(msg), mdPath


def setup(inp_dv, inp_tk):
    """...

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
        It is `True` if the metadata template fits the expectations and `False` if it does not.
    """

    ds.from_json(read_file(md))
    resp = ds.validate_json()

    return resp


def deposit_ds(api, inp_dv, ds):
    """
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

    # upload_file()

    return dsStatus, dsPID, dsID, dsPURL


# def upload_file():
#     """
#     Parameters
#     ----------

#     Returns
#     -------

#     """


# Save metadata:
def save_md(item, atr, val, session):
    # instead of obj, use path and name that is changes to iRODS object
    obj = session.data_objects.get(f"{item}")
    obj.metadata.apply_atomic_operations(
        AVUOperation(operation="add", avu=iRODSMeta(f"{atr}", f"{val}"))
    )
