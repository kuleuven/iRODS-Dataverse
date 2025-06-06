from irods2dataverse import from_irods, to_dataverse, direct_upload, avu2json, cli_input
import json
import maskpass
import datetime
import tempfile
import shutil
import time

import os.path
from rich.console import Console
from rich.style import Style
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.padding import Padding


# Test with 2 files /set/home/datateam_set/iRODS2DV/20240718_demo
# Use DVUploader and Include an option on which upload method should be chosen.

# Dataverse installations are pre-configured, using customClass.py and customization.ini.
# This script implements the perspective where the individual data objects destined for publication are either annotated with metadata or their path is provided.
# Another perspective that could be explored is the case where the dataset is all in a pre-specified iRODS collection and the structure is mirrored in Dataverse.

# define custom colors
info = Style(color="cyan")
action = Style(color="yellow")
warning = Style(color="red")


# create a rich console
c = Console()


def vertical_space(text, style="default", below=0, left=1):
    return c.print(Padding(text, (1, left, below, 0), style=style))


# --- Print instructions for the metadata-driven process --- #
c.print(
    Panel.fit(
        """
This is an implementation for programmatic publication of data from iRODS into a Dataverse installation.
        
To drive the process based on metadata, go to your selected zone and add the following metadata to at 
least one data object for a configured Dataverse installation (e.g. Demo):      
       
    A: dv.publication   V: initiated                                         
    A: dv.installation  V: Demo

The configured Dataverse installations are: Demo, RDR, RDR-pilot  

For more detailed instructions go to https://github.com/kuleuven/iRODS-Dataverse
                   """,
        title="Instructions",
    )
)


if __name__ == "__main__":
    # --- Provide the iRODS environment file to authenticate in a specific zone --- #

    vertical_space("Authenticate to iRODS zone...")
    session = from_irods.authenticate_iRODS(
        os.path.expanduser("~") + "/.irods/irods_environment.json"
    )
    if session:
        c.print("You are now authenticated to iRODS", style=info)
    else:
        raise SystemExit

    # --- Select Data: if there is no metadata specifying the object that needs to be published, ask user to provide the path --- #
    time.sleep(0.5)
    vertical_space(
        "Select data in iRODS, via attached metadata in iRODS or via iRODS paths as typed input"
    )

    atr_publish = "dv.publication"
    val = "initiated"

    data_objects_list = from_irods.query_data(
        atr_publish, val, session
    )  # look for data based on A = dv.publication & value = initiated

    if len(data_objects_list) > 0:
        c.print(
            f"Metadata with attribute <{atr_publish}> and value <{val}> are found in iRODS.",
            style=info,
        )
    else:
        c.print(
            f"No metadata with attribute <{atr_publish}> and value <{val}> are found.",
            style=info,
        )
        while True:
            vertical_space("")
            inp_i = Prompt.ask(
                "Provide the full iRODS path and name of the data object. To add multiple objects use a list ['path1', 'path2']. Press Enter to submit. Leave blank and press Enter to end."
            )
            if not inp_i and len(data_objects_list) > 0:
                break
            try:
                list_input = cli_input.to_list(inp_i)
                for item in list_input:
                    obj = session.data_objects.get(item)
                    data_objects_list.append(obj)
                    if from_irods.save_md(obj, atr_publish, val, op="set"):
                        c.print(
                            f"Metadata with attribute <{atr_publish}> and value <{val}> are added in the selected data object."
                        )
                    else:
                        c.print(
                            f"Failed to add or set metadata in iRODS",
                            style=warning,
                        )
            except Exception as e:  # change this to specific exception
                c.print(
                    f"The path of the data object is not correct. Please provide a correct path. \n Hint: /zone/home/collection/filename",
                    style=warning,
                )

    time.sleep(0.5)
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
        from_irods.save_md(item, atr_publish, "processed", op="set")
        # Dataset status timestamp
        from_irods.save_md(
            item, "dv.publication.timestamp", datetime.datetime.now(), op="set"
        )
        vertical_space("")

    time.sleep(0.5)

    vertical_space(
        f"Metadata attribute <{atr_publish}> is updated to <processed> for the selected objects.",
        style=info,
    )

    # --- Select Dataverse: if there is no object metadata specifying the Dataverse installation, ask for user input --- #
    vertical_space(
        "Select one of the configured Dataverse installations, via attached metadata in iRODS or via typed input."
    )
    atr_dataverse = "dv.installation"
    installations = ["RDR", "Demo", "RDR-pilot"]
    ldv = from_irods.query_dv(atr_dataverse, data_objects_list, installations)
    if len(ldv) == 1 and "missing" not in ldv:
        input_dataverse = list(ldv.keys())[0]
        vertical_space(
            f"Metadata with attribute <{atr_dataverse}> and value <{input_dataverse}> for the selected data objects are found in iRODS.",
            style=info,
        )
    else:
        if len(ldv) > 1:
            vertical_space(
                f"Not all the data objects are assigned to the same installation."
            )
        else:
            vertical_space(
                f"The selected objects have no attribute <{atr_dataverse}>.",
                style=action,
            )
        data_objects_list = []
        input_dataverse = Prompt.ask(
            "Specify the configured Dataverse installation to publish the data",
            choices=installations,
            default="Demo",
        )
        if input_dataverse in ldv:
            data_objects_list = ldv[input_dataverse]
            c.print(
                f"{len(ldv[input_dataverse])} items were tagged for this installation."
            )
        if "missing" in ldv:
            if len(ldv) > 1:
                add_missing = Confirm.ask(
                    f"{len(ldv['missing'])} data objects had no metadata for the installation. Would you still want to submit them to this Dataverse installation?"
                )
            else:
                add_missing = True
            if add_missing:
                for item in ldv["missing"]:
                    from_irods.save_md(item, atr_dataverse, input_dataverse, op="set")
                    data_objects_list.append(item)
                c.print(
                    f"Metadata with attribute <{atr_dataverse}> and value <{input_dataverse}> are added in the selected data objects.",
                    style=action,
                )

    # --- Set-up for the selected Dataverse installation --- #
    vertical_space(
        f"Provide your Token for <{input_dataverse}> Dataverse installation or the name of its environment variable."
    )
    token = maskpass.askpass(prompt="", mask="*")
    token = os.getenv(token, token)

    # --- Validate that the selected Dataverse installations is configured and create a Dataset --- #
    ds = to_dataverse.get_dataset(input_dataverse)
    path_to_schema = ds.mango_schema
    path_to_template = ds.metadata_template

    # --- Create a Dataverse session --- #
    api = to_dataverse.authenticate_DV(ds.baseURL, token)

    # --- Provide information on the obligatory metadata --- #
    vertical_space(
        f"Minimum metadata should be provided to proceed with the publication.\nThe metadata template can be found in {path_to_template}."
    )

    # --- Retrieve filled-in metadata --- #
    def ask_metadata(path_to_template, path_to_schema, data_objects_list):
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
            md = avu2json.get_template(path_to_template, metadata)
        elif Confirm.ask(
            "Would you like to provide the necessary metadata using the command line interface?\n"
        ):
            md_path = cli_input.fill_in_md_template(path_to_template)
            with open(md_path, "r") as f:
                md = json.load(f)
            # shutil.rmtree(md_path[:-14])

        else:
            md = ""
            while not os.path.exists(md):
                md = Prompt.ask(
                    f"""Provide the path for the filled-in Dataset metadata. This JSON file can either match the template <{path_to_template}> or be the simplified (short JSON) version.""",
                    default=path_to_template,
                )
            with open(md, "r") as f:
                try:
                    md = json.load(f)
                except:
                    raise IOError("The file could not be read. Is this a valid JSON?")
                if "datasetVersion" not in md:
                    try:
                        md = avu2json.get_template(path_to_template, md)
                    except:
                        raise ValueError("The JSON is not in the correct format.")

        return md

    # --- Validate metadata --- #
    md = ask_metadata(path_to_template, path_to_schema, data_objects_list)
    vmd = to_dataverse.validate_md(ds, md)
    while not (vmd):
        vertical_space(
            f"The metadata are not validated, modify <{md}>, save and hit enter to continue.",
            style=info,
        )
        md = ask_metadata(path_to_template, path_to_schema, data_objects_list)
        vmd = to_dataverse.validate_md(ds, md)
    vertical_space(f"The metadata are validated, the process continues.", style=info)

    # --- Deposit draft in selected Dataverse installation --- #
    dsStatus, dsPID, dsID = to_dataverse.deposit_ds(api, ds)
    vertical_space(
        f"The Dataset publication metadata are: status = {dsStatus}, PID = {dsPID}, dsID = {dsID}",
        style=info,
    )

    # --- Add metadata in iRODS --- #
    for item in data_objects_list:
        vertical_space("")
        # Dataset DOI
        from_irods.save_md(item, "dv.ds.DOI", dsPID, op="add")
        # # Dataset PURL
        # from_irods.save_md(item, "dv.ds.PURL", dsPURL, op="set")

    vertical_space(
        f"The Dataset DOI is added as metadata to the selected data objects.",
        style=info,
    )

    # --- Upload data files --- #
    trg_path = tempfile.mkdtemp("dataverse_files")

    if input_dataverse == "Demo":
        ## OPTION 1: LOCAL DOWNLOAD (for Demo installation)
        for item in data_objects_list:
            vertical_space("")
            # Save data locally
            from_irods.save_df(item, trg_path, session)  # download object locally
            # Upload file(s)
            md = to_dataverse.deposit_df(api, dsPID, item.name, trg_path)
            # Update status of publication in iRODS from 'processed' to 'deposited'
            from_irods.save_md(item, atr_publish, "deposited", op="set")
            # Update timestamp
            from_irods.save_md(
                item, "dv.publication.timestamp", datetime.datetime.now(), op="set"
            )
        shutil.rmtree(trg_path)
    else:
        ## OPTION 2: DIRECT UPLOAD (for RDR and RDR-pilot)
        # --- Create information to pass on the header for direct upload --- #
        header_key, header_ct = direct_upload.create_headers(token)
        for item in data_objects_list:
            vertical_space("")
            objChecksum, objMimetype, objSize = from_irods.get_object_info(item)
            fileURL, storageID = direct_upload.get_du_url(
                ds.baseURL, dsPID, objSize, header_key
            )
            du_step2 = direct_upload.put_in_s3(item, fileURL, header_ct)
            md_dict = direct_upload.create_du_md(
                storageID, item.name, objMimetype, objChecksum
            )
            du_step3 = direct_upload.post_to_ds(md_dict, ds.baseURL, dsPID, header_key)
            # Update status of publication in iRODS from 'processed' to 'deposited'
            from_irods.save_md(item, atr_publish, "deposited", op="set")
            # Update timestamp
            from_irods.save_md(
                item, "dv.publication.timestamp", datetime.datetime.now(), op="set"
            )
            from_irods.save_md(
                item,
                "dv.df.storageIdentifier",
                storageID,
                op="add",
            )  # TO DO: for the metadata that are added and not set, make a repeatable composite field to group them together

    # # Add metadata in iRODS
    # from_irods.save_md(
    #     f"{objPath[i]}/{objName[i]}", "dv.df.id", df_id, session, op="set"
    # )

    vertical_space(
        f"Metadata attribute <{atr_publish}> is updated to <deposited> for the selected data objects.",
        style=info,
    )

    # Additional metadata could be extracted from the filled-in Dataverse metadata template (e.g. author information)

    # Next step - 1: Publication / Send for review via Dataverse installation UI
    # The current agreement is to send for publication via the Dataverse UI.
    # This is because different procedures may apply in each Dataverse installation.

    # Next step - 2: Update the metadata in iRODS
    # From the iRODS side, to update the status of the publication (atr_publish) from deposited to "published", we need to check the situation in Dataverse.
    # With periodic checks, query for the DOI of the dataset and check in the metadata if the dataset is published.
    # We have talked about running checksums to see if the publication data are altered outside iRODS.

    # Clean-up iRODS session
    session.cleanup()
