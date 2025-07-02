"""Retrieve data and metadata from iRODS regarding target Dataverse deposit"""

from typing import Tuple
import magic
from irods.session import iRODSSession
from irods.column import Criterion
from irods.data_object import iRODSDataObject
from irods.models import Collection, DataObject, DataObjectMeta
import irods.keywords as kw


def query_data(atr: str, val: str, session: iRODSSession) -> list[iRODSDataObject]:
    """iRODS query to get the data objects destined for publication based on metadata"""

    query_results = (
        session.query(Collection.name, DataObject.name)
        .filter(Criterion("=", DataObjectMeta.name, atr))
        .filter(Criterion("=", DataObjectMeta.value, val))
        # TODO add optional units using filter object
    )

    data_object_paths = set(
        f"{item[Collection.name]}/{item[DataObject.name]}" for item in query_results
    )
    return [session.data_objects.get(path) for path in data_object_paths]


def get_object_info(obj: iRODSDataObject) -> Tuple[str, str, str]:
    """Retrieve object information for direct upload"""

    # Get the checksum value from iRODS
    object_checksum = obj.chksum()[5:]  # this is algorithm-specific

    # Get the mimetype (from paul, mango portal)
    with obj.open("r") as f:
        blub = f.read(50 * 1024)
        object_mimetype = magic.from_buffer(blub, mime=True)

    # Get the path of the file in the project (to be replicated in Dataverse)
    path_relative_to_root = "/".join(obj.path.split("/")[4:-1])

    return object_checksum, object_mimetype, path_relative_to_root


def save_metadata(
    data_object: iRODSDataObject,
    metadata_name: str,
    metadata_value: str,
    operation: str,
):
    """Add metadata in iRODS"""

    try:
        if operation == "add":
            data_object.metadata.add(str(metadata_name), str(metadata_value))
            print(
                f"Metadata attribute {metadata_name} with value {metadata_value}> is added to data object {data_object}."
            )
            return True
        elif operation == "set":
            data_object.metadata.set(f"{metadata_name}", f"{metadata_value}")
            print(
                f"Metadata attribute {metadata_name} is set to <{metadata_value}> for data object {data_object}."
            )
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


def save_to_local_file(
    data_object: iRODSDataObject,
    target_path: str,
    session: iRODSSession,
):
    """Save locally the iRODS data objects destined for publication
    Used for installations that do not support direct upload (Demo)"""

    opts = {kw.FORCE_FLAG_KW: True}
    # TO DO: checksum in case download is not needed?

    session.data_objects.get(
        data_object.path, f"{target_path}/{data_object.name}", **opts
    )
