import datetime
import json
import os.path
import shutil
import tempfile
from time import sleep

import maskpass
from irods.session import iRODSSession
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.style import Style
from rich.table import Table

from irods2dataverse import avu2json, cli_input, direct_upload, from_irods, to_dataverse

# Define custom colors
info = Style(color="cyan")
action = Style(color="yellow")
warning = Style(color="red")


# Create a rich console
c = Console()


def vertical_space(text, style: Style | str = "default", below=0, left=1):
    return c.print(Padding(text, (1, left, below, 0), style=style))


# --- Print instructions for the metadata-driven process --- #
c.print(
    Panel.fit(
        """This is an implementation for programmatic publication of data from iRODS into a Dataverse installation. 
        
        To drive the process based on metadata, go to your selected zone and add the following metadata to 
        at least one data object for a configured Dataverse installation (e.g. Demo):
        
        A: dv.publication   V: initiated
        A: dv.installation  V: Demo
        
        The configured Dataverse installations are: Demo, RDR, RDR-pilot
        
        For more detailed instructions go to https://github.com/kuleuven/iRODS-Dataverse""",
        title="Instructions",
    )
)


if __name__ == "__main__":
    # --- Provide the iRODS environment file to authenticate in a specific zone --- #

    vertical_space("Authenticate to iRODS zone...")
    try:
        env_file = os.getenv(
            "IRODS_ENVIRONMENT_FILE",
            os.path.expanduser("~") + "/.irods/irods_environment.json",
        )
        session = iRODSSession(irods_env_file=env_file)
        c.print("You are now authenticated to iRODS", style=info)
    except Exception as e:
        raise ValueError(e) from e

    # --- Select Data: if there is no metadata specifying the object that needs to be published, ask user to provide the path --- #
    sleep(0.5)
    vertical_space(
        "Select data in iRODS, via attached metadata in iRODS or via iRODS paths as typed input"
    )

    METADATA_ATTRIBUTE_STATUS = "dv.publication"
    METADATA_ATTRIBUTE_TIME = "dv.publication.timestamp"
    METADATA_ATTRIBUTE_DOI = "dv.ds.DOI"
    # METADATA_ATTRIBUTE_PURL = "dv.ds.PURL"

    metadata_status_value = "initiated"

    data_objects_list = from_irods.query_data(
        METADATA_ATTRIBUTE_STATUS, metadata_status_value, session
    )  # look for data based on A = dv.publication & value = initiated

    if len(data_objects_list) > 0:
        c.print(
            f"Metadata with attribute <{METADATA_ATTRIBUTE_STATUS}> and value <{metadata_status_value}> are found in iRODS.",
            style=info,
        )
    else:
        c.print(
            f"No metadata with attribute <{METADATA_ATTRIBUTE_STATUS}> and value <{metadata_status_value}> are found.",
            style=info,
        )
        while True:
            vertical_space("")
            input_item = Prompt.ask(
                "Provide the full iRODS path and name of the data object. To add multiple objects use a list ['path1', 'path2']. Press Enter to submit. Leave blank and press Enter to end."
            )
            if not input_item and len(data_objects_list) > 0:
                break
            try:
                list_input = cli_input.to_list(input_item) if isinstance(input_item, list) else [input_item]
                for item in list_input:
                    irods_object = session.data_objects.get(item)
                    data_objects_list.append(irods_object)
                    if from_irods.save_metadata(
                        irods_object,
                        METADATA_ATTRIBUTE_STATUS,
                        metadata_status_value,
                        operation="set",
                    ):
                        c.print(
                            f"Metadata with attribute <{METADATA_ATTRIBUTE_STATUS}> and value <{metadata_status_value}> are added in the selected data object."
                        )
                    else:
                        c.print(
                            "Failed to add or set metadata in iRODS",
                            style=warning,
                        )
            except Exception:
                c.print(
                    "The path of the data object is not correct. Please provide a correct path. \n Hint: /zone/home/collection/filename",
                    style=warning,
                )

    sleep(0.5)
    # --- Print a table of the selected data --- #
    c.print("The following objects are selected for publication:", style=info)
    table = Table(title="data object overview")
    table.add_column("unique id", justify="right", no_wrap=True)
    table.add_column("name")
    table.add_column("size (MB)", justify="right")
    for object in data_objects_list:
        table.add_row(f"{object.id}", f"{object.name}", f"{object.size/1000000:.2f}")
    c.print(table)

    # --- Update metadata in iRODS from initiated to processed & add timestamp --- #

    for item in data_objects_list:
        # Update status of publication in iRODS from 'initiated' to 'processed'
        from_irods.save_metadata(
            item, METADATA_ATTRIBUTE_STATUS, "processed", operation="set"
        )
        # Dataset status timestamp
        from_irods.save_metadata(
            item,
            METADATA_ATTRIBUTE_TIME,
            str(datetime.datetime.now()),
            operation="set",
        )
        vertical_space("")

    sleep(0.5)

    vertical_space(
        f"Metadata attribute <{METADATA_ATTRIBUTE_STATUS}> is updated to <processed> for the selected objects.",
        style=info,
    )

    # --- Select Dataverse: if there is no object metadata specifying the Dataverse installation, ask for user input --- #
    vertical_space(
        "Select one of the configured Dataverse installations, via attached metadata in iRODS or via typed input."
    )
    METADATA_ATTRIBUTE_INSTALLATION = "dv.installation"
    installations_list = ["RDR", "Demo", "RDR-pilot"]
    input_dataverse = Prompt.ask(
        "Specify the configured Dataverse installation to publish the data",
        choices=installations_list,
        default="Demo",
    )

    for item in data_objects_list:
        from_irods.save_metadata(
            item, METADATA_ATTRIBUTE_INSTALLATION, input_dataverse, operation="set"
        )

    # --- Set-up for the selected Dataverse installation --- #
    vertical_space(
        f"Provide your Token for <{input_dataverse}> Dataverse installation or the name of its environment variable."
    )
    DATAVERSE_TOKEN = maskpass.askpass(prompt="", mask="*")
    DATAVERSE_TOKEN = os.getenv(DATAVERSE_TOKEN, DATAVERSE_TOKEN)

    # --- Validate that the selected Dataverse installations is configured and create a Dataset --- #
    dataverse_dataset = to_dataverse.get_dataset(input_dataverse)
    path_to_schema = dataverse_dataset.mango_schema
    path_to_template = dataverse_dataset.metadata_template

    # --- Create a Dataverse session --- #
    api = to_dataverse.authenticate_to_dataverse(
        dataverse_dataset.baseURL, DATAVERSE_TOKEN
    )

    # --- Provide information on the obligatory metadata --- #
    vertical_space(
        f"Minimum metadata should be provided to proceed with the publication.\nThe metadata template can be found in {path_to_template}."
    )

    # --- Retrieve filled-in metadata --- #
    def ask_metadata(
        path_to_template: str, path_to_schema: str, data_objects_list: list
    ) -> dict:
        """..."""
        if Confirm.ask(
            "Are you ManGO user and have you filled in the ManGO metadata schema for your Dataverse installation?\n"
        ):
            # get metadata
            for data_object in data_objects_list:
                metadata = avu2json.parse_mango_metadata(path_to_schema, data_object)
                if metadata:
                    break
            # get template
            if not metadata:
                c.print(
                    "Sorry, no schema metadata for this Dataverse installation was found, let's try again!"
                )
                return ask_metadata(path_to_template, path_to_schema, data_objects_list)
            dataset_metadata = avu2json.get_template(path_to_template, metadata)
        elif Confirm.ask(
            "Would you like to provide the necessary metadata using the command line interface?\n"
        ):
            dataset_metadata = cli_input.fill_in_md_template(path_to_template)
        else:
            dataset_metadata = ""
            while not os.path.exists(dataset_metadata):
                dataset_metadata = Prompt.ask(
                    f"""Provide the path for the filled-in Dataset metadata. This JSON file can either match the template <{path_to_template}> or be the simplified (short JSON) version.""",
                    default=path_to_template,
                )
            with open(dataset_metadata, "r") as f:
                try:
                    dataset_metadata = json.load(f)
                except Exception:
                    raise IOError("The file could not be read. Is this a valid JSON?")
                if "datasetVersion" not in dataset_metadata:
                    try:
                        dataset_metadata = avu2json.get_template(
                            path_to_template, dataset_metadata
                        )
                    except Exception:
                        raise ValueError("The JSON is not in the correct format.")

        return dataset_metadata

    # --- Validate metadata --- #
    validated_metadata_template = False
    template_is_validated = False  # the template is checked
    while not (validated_metadata_template):
        if template_is_validated:
            vertical_space(
                "The metadata template is not validated, provide a valid metadata template, "
                "save and hit enter to continue.",
                style=info,
            )

        metadata_template = ask_metadata(
            str(path_to_template), str(path_to_schema), data_objects_list
        )
        validated_metadata_template = to_dataverse.validate_dataset_metadata_template(
            dataverse_dataset, metadata_template
        )
        template_is_validated = True

    vertical_space(
        "The metadata template is validated, the process continues.", style=info
    )

    # --- Deposit draft in selected Dataverse installation --- #
    api_response = api.create_dataset(
        dataverse_dataset.alias, dataverse_dataset.json()
    ).json()
    dataset_persistent_id = api_response["data"]["persistentId"]

    # vertical_space(
    #     f"The Dataset publication PID = {dataset_persistent_id}",
    #     style=info,
    # )

    # --- Add metadata in iRODS --- #
    for item in data_objects_list:
        vertical_space("")
        # Dataset DOI
        from_irods.save_metadata(
            item, METADATA_ATTRIBUTE_DOI, dataset_persistent_id, operation="add"
        )
        # # Dataset PURL
        # from_irods.save_metadata(item, METADATA_ATTRIBUTE_PURL, dsPURL, op="set")

    vertical_space(
        "The Dataset DOI is added as metadata to the selected data objects.",
        style=info,
    )

    # --- Upload data files --- #
    local_path = tempfile.mkdtemp("dataverse_files")

    if input_dataverse == "Demo":
        # OPTION 1: LOCAL DOWNLOAD (for Demo installation)
        for item in data_objects_list:
            vertical_space("")
            # Save data locally
            from_irods.save_to_local_file(
                item, local_path, session
            )  # download object locally, only for Demo
            # Upload file(s)
            metadata_template = to_dataverse.deposit_datafile(
                api, dataset_persistent_id, item.name, local_path
            )
            # Update status of publication in iRODS from 'processed' to 'deposited'
            from_irods.save_metadata(
                item, METADATA_ATTRIBUTE_STATUS, "deposited", operation="set"
            )
            # Update timestamp
            from_irods.save_metadata(
                item,
                METADATA_ATTRIBUTE_TIME,
                str(datetime.datetime.now()),
                operation="set",
            )
        shutil.rmtree(local_path)
    else:
        # OPTION 2: DIRECT UPLOAD (for RDR and RDR-pilot)
        # --- Create information to pass on the header for direct upload --- #
        header_key = {
            "X-Dataverse-key": DATAVERSE_TOKEN,
        }
        for item in data_objects_list:
            vertical_space("")

            file_url, storage_id = direct_upload.get_direct_upload_url(
                dataverse_dataset.baseURL,
                dataset_persistent_id,
                item.size + 1,
                header_key,  # TODO check why + 1 (empty files?)
            )
            put_in_s3_response = direct_upload.put_in_s3(item, file_url)
            metadata_dictionary = direct_upload.create_direct_upload_metadata(
                storage_id, item
            )
            post_to_dataset_response = direct_upload.post_to_dataset(
                metadata_dictionary,
                dataverse_dataset.baseURL,
                dataset_persistent_id,
                header_key,
            )
            # Update status of publication in iRODS from 'processed' to 'deposited'
            from_irods.save_metadata(
                item, METADATA_ATTRIBUTE_STATUS, "deposited", operation="set"
            )
            # Update timestamp
            from_irods.save_metadata(
                item,
                METADATA_ATTRIBUTE_TIME,
                str(datetime.datetime.now()),
                operation="set",
            )
            from_irods.save_metadata(
                item,
                "dv.df.storageIdentifier",
                storage_id,
                operation="add",
            )

    vertical_space(
        f"Metadata attribute <{METADATA_ATTRIBUTE_STATUS}> is updated to <deposited> for the selected data objects.",
        style=info,
    )

    # Clean-up iRODS session
    session.cleanup()
