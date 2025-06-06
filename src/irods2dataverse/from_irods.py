import os
import json
import magic
from irods.session import iRODSSession
from irods.column import Criterion
from irods.models import Collection, DataObject, DataObjectMeta
import irods.keywords as kw


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
    return list(lobj)


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
