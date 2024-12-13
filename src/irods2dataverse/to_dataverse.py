import json
from pyDataverse.api import NativeApi
from pyDataverse.models import Datafile
from pyDataverse.utils import read_file
from configparser import ConfigParser


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
    api: list
        object of class pyDataverse.api.NativeApi
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


def deposit_ds(api, ds):
    """Create a Dataverse dataset with user specified metadata

    Parameters
    ----------
    api : list
        Status and pyDataverse object
    ds: Dataset
        The Dataset for the selected Dataverse installation

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

    resp = api.create_dataset(ds.alias, ds.json()).json()
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
