"""Interacts with the Dataverse installation to initiate a deposit"""

from typing import Container, Tuple
import json
from importlib.resources import files
from pyDataverse.api import NativeApi
from pyDataverse.models import Datafile
from pyDataverse.utils import read_file
from configparser import ConfigParser


def authenticate_to_dataverse(dataverse_url: str, dataverse_token: str) -> NativeApi:
    """Establish a session for the selected Dataverse installation"""

    api = NativeApi(dataverse_url, dataverse_token)
    resp = api.get_info_version()

    if resp.status_code != 200:
        raise ConnectionRefusedError(
            "The authentication to the selected Dataverse installation failed."
        )
    return api


def instantiate_selected_class(
    installation_name: str, config: ConfigParser
) -> Container:
    """Instantiate Dataset class based on selected Dataverse installation"""

    config_section = config[installation_name]
    modulename, classname = config_section["className"].split(".", 2)
    importlib = __import__("importlib")
    module = importlib.import_module(f"irods2dataverse.{modulename}")
    selected_class = getattr(module, classname)

    return selected_class()


def get_dataset(input_dataverse: str) -> Container:
    """Create an empty dataset in the selected Dataverse installation"""

    # Read once the configuration file located in a hard-coded path
    config = ConfigParser()
    config.read(str(files("resources").joinpath("customization.ini")))
    # Check that the Dataverse installation is configured
    try:
        # Instantiate the Dataset class of the selected Dataverse installation
        dataset_instance = instantiate_selected_class(input_dataverse, config)
        print("The selected Dataverse installation is configured")
    except Exception as e:
        if input_dataverse not in config.sections():
            print("The Dataverse installation you selected is not configured.")
        print(type(e))
        print(f"An error occurred: {e}")

    return dataset_instance


def validate_dataset_metadata(dataset: Container, metadata_template: str) -> bool:
    """Check the metadata template is up-to-date"""

    if isinstance(metadata_template, str):
        # metadata_template is given as a path
        metadata_template = read_file(metadata_template)
    elif isinstance(metadata_template, dict):
        # metadata template is given as a dictionary
        metadata_template = json.dumps(metadata_template)
    try:
        dataset.from_json(metadata_template)
        return dataset.validate_json()  # True
    except Exception as e:
        print(type(e))
        print(f"An error occurred: {e}")
        return False


def deposit_dataset(api: NativeApi, dataset: Container) -> Tuple[str, str, str]:
    """Create a Dataverse dataset with user specified metadata"""

    resp = api.create_dataset(dataset.alias, dataset.json()).json()
    dataset_status = resp["status"]
    dataset_persistent_identifier = resp["data"]["persistentId"]
    dataset_identifier = resp["data"]["id"]
    # resp = api.create_dataset_private_url(dsPID)
    # dataset_private_url = resp.json()["data"]["link"]
    # RDR does not allow PURL creation; move to Class definition?

    return (
        dataset_status,
        dataset_persistent_identifier,
        dataset_identifier,
    )  # dataset_private_url


def deposit_datafile(
    api: NativeApi,
    dataset_persistent_identifier: str,
    data_object_name: str,
    inp_path: str,
) -> dict:
    """Upload the list of data files in Dataverse Dataset"""

    datafile = Datafile()
    datafile.set({"pid": dataset_persistent_identifier, "filename": data_object_name})
    datafile.get()
    resp = api.upload_datafile(
        dataset_persistent_identifier, f"{inp_path}/{data_object_name}", datafile.json()
    )

    print(f"{data_object_name} is uploaded")

    return resp.json()
