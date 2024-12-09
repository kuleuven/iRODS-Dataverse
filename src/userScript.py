from irods2dataverse import functions
from irods2dataverse import avu2json
import json
import maskpass
import datetime
import os.path
from rich.console import Console
from rich.style import Style
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table


# Test with 2 files /set/home/datateam_set/iRODS2DV/20240718_demo
# Use DVUploader and Include an option on which upload method should be chosen.

# Dataverse installations are pre-configured, using customClass.py and customization.ini.
# This script implements the perspective where the individual data objects destined for publication are either annotated with metadata or their path is provided.
# Another perspective that could be explored is the case where the dataset is all in a pre-specified iRODS collection and the structure is mirrored in Dataverse.

# define custom colors
info = Style(color="cyan")
action = Style(color="yellow")
warning = Style(color="red")
panel_blue = Style(color="white", bold=True, bgcolor="blue")
panel_black = Style(color="white", bgcolor="black")

# create a rich console
c = Console()

# --- Print instructions for the metadata-driven process --- #
c.print(
    Panel.fit(
        """
 To drive the process based on metadata, go to your selected zone 
 and add the following metadata to at least one data object 
 for a configured Dataverse installation (e.g. Demo):             
    A: dv.publication   V: initiated                                         
    A: dv.installation  V: Demo
The configured Dataverse installations are: Demo, RDR, RDR-pilot  
                   """,
        style=panel_blue,
        title="Instructions",
    )
)


# --- Provide the iRODS environment file to authenticate in a specific zone --- #

print("\nAuthenticate to iRODS zone...")
session = functions.authenticate_iRODS(
    os.path.expanduser("~") + "/.irods/irods_environment.json"
)
if session:
    c.print("You are now authenticated to iRODS", style=info)
else:
    raise SystemExit


# --- Select Data: if there is no metadata specifying the object that needs to be published, ask user to provide the path --- #

print(
    "Select data in iRODS, via attached metadata in iRODS or via iRODS paths as typed input"
)

atr_publish = "dv.publication"
val = "initiated"


data_objects_list = functions.query_data(
    atr_publish, val, session
)  # look for data based on A = dv.publication & value = initiated

if len(data_objects_list) == 0:  # ldt = qdata
    c.print(
        f"No metadata with attribute <{atr_publish}> and value <{val}> are found.",
        style=info,
    )
    add = True
    while add:
        inp_i = input(
            "Provide the full iRODS path and name of the data object to be published in one of the configured Dataverse installations:\n"
        )
        try:
            obj = session.data_objects.get(inp_i)
            data_objects_list.append(obj)
            if functions.save_md(obj, atr_publish, val, op="set"):
                c.print(
                    f"Metadata with attribute <{atr_publish}> and value <{val}> are added in the selected data object."
                )
            else:
                c.print(
                    f"The path of the data object is not correct. Please provide a correct path. \n Hint: /zone/home/collection/folder/filename",
                    style=warning,
                )
        except Exception as e:  # change this to specific exception
            c.print(
                f"The path of the data object is not correct. Please provide a correct path. \n Hint: /zone/home/collection/folder/filename",
                style=warning,
            )
        add = Confirm.ask("Add more objects? y/n\n")
else:
    c.print(
        f"Metadata with attribute <{atr_publish}> and value <{val}> are found in iRODS.",
        style=info,
    )


# --- Print a table of the selected data --- #
c.print("The following objects are selected for publication:", style=info)
table = Table(title="data object overview")
table.add_column("unique id", justify="right", style="cyan", no_wrap=True)
table.add_column("name", style="magenta")
table.add_column("size (MB)", justify="right", style="green")
for object in data_objects_list:
    table.add_row(f"{object.id}", f"{object.name}", f"{object.size/1000000:.2f}")
c.print(table)


# --- Update metadata in iRODS from initiated to processed & add timestamp --- #

for item in data_objects_list:
    # Update status of publication in iRODS from 'initiated' to 'processed'
    functions.save_md(item, atr_publish, "processed", op="set")
    # Dataset status timestamp
    functions.save_md(
        item, "dv.publication.timestamp", datetime.datetime.now(), op="set"
    )

c.print(
    f"Metadata attribute <{atr_publish}> is updated to <processed> for the selected objects.",
    style=info,
)

# --- Select Dataverse: if there is no object metadata specifying the Dataverse installation, ask for user input --- #
print(
    "Select one of the configured Dataverse installations, via attached metadata in iRODS or via typed input."
)
atr_dv = "dv.installation"
installations = ["RDR", "Demo", "RDR-pilot"]
ldv = functions.query_dv(atr_dv, data_objects_list, installations)
if len(ldv) == 1 and "missing" not in ldv:
    inp_dv = list(ldv.keys())[0]
    c.print(
        f"Metadata with attribute <{atr_dv}> and value <{inp_dv}> for the selected data objects are found in iRODS.",
        style=info,
    )
else:
    if len(ldv) > 1:
        c.print(f"Not all the data objects are assigned to the same installation.")
    else:
        c.print(f"The selected objects have no attribute <{atr_dv}>.", style=action)
    data_objects_list = []
    inp_dv = Prompt.ask(
        "Specify the configured Dataverse installation to publish the data",
        choices=installations,
        default="Demo",
    )
    if inp_dv in ldv:
        data_objects_list = ldv[inp_dv]
        c.print(f"{len(ldv[inp_dv])} items were tagged for this installation.")
    if "missing" in ldv:
        add_missing = Confirm.ask(
            f"{len(ldv['missing'])} items were tagged with no installation. Would you like to include them?"
        )
        if add_missing:
            for item in ldv["missing"]:
                functions.save_md(item, atr_dv, inp_dv, op="set")
                data_objects_list.append(item)
            c.print(
                f"Metadata with attribute <{atr_dv}> and value <{inp_dv}> are added in the selected data objects.",
                style=action,
            )


# --- Set-up for the selected Dataverse installation --- #
print(
    f"Provide your Token for <{inp_dv}> Dataverse installation or the name of its environment variable."
)
token = maskpass.askpass(prompt="", mask="*")
token = os.getenv(token, token)
api, ds = functions.setup(
    inp_dv, token
)  # this function also validates that the selected Dataverse installations is configured.

# get the path for the first data object in the list
# check the metadata only from the first object in the list
# print(logical_path.path)
path_to_schema = ds.mango_schema
path_to_template = ds.metadata_template

# --- Create information to pass on the header for direct upload --- #
header_key, header_ct = functions.create_headers(token)


# --- Retrieve filled-in metadata --- #
if Confirm.ask(
    "Are you ManGO user and have you filled in the ManGO metadata schema for your Dataverse installation?\n"
):
    # get metadata
    metadata = avu2json.parse_mango_metadata(path_to_schema, data_objects_list[0])
    # get template
    md = functions.get_template(path_to_template, metadata)

else:
    md = ""
    while not os.path.exists(md):
        md = Prompt.ask(
            f"""Provide the path for the filled-in Dataset metadata. This JSON file can either match the template <{path_to_template}> or be a simplified version.""",
            default=path_to_template,
        )
    with open(md, "r") as f:
        try:
            md_contents = json.load(f)
        except:
            raise IOError("The file could not be read. Is this a valid JSON?")
        if "datasetVersion" not in md_contents:
            try:
                metadata = avu2json.parse_json_metadata(path_to_schema, md_contents)
                md = functions.get_template(path_to_template, metadata)
            except:
                raise ValueError("The JSON is not in the correct format.")

# --- Validate metadata --- #
vmd = functions.validate_md(ds, md)
while not (vmd):
    c.print(
        f"The metadata are not validated, modify <{md}>, save and hit enter to continue [PLACEHOLDER - see avu2json].",
        style=info,
    )
    md = input()
    vmd = functions.validate_md(ds, md)
c.print(f"The metadata are validated, the process continues.", style=info)

# --- Deposit draft in selected Dataverse installation --- #
dsStatus, dsPID, dsID = functions.deposit_ds(api, ds.alias, ds)
c.print(
    f"The Dataset publication metadata are: status = {dsStatus}, PID = {dsPID}, dsID = {dsID}",
    style=info,
)

# --- Add metadata in iRODS --- #
for item in data_objects_list:
    # Dataset DOI
    functions.save_md(item, "dv.ds.DOI", dsPID, op="add")
    # # Dataset PURL
    # functions.save_md(item, "dv.ds.PURL", dsPURL, op="set")


c.print(
    f"Metadata attribute <{atr_publish}> is updated to <deposited> for the selected data objects.",
    style=info,
)
c.print(
    f"The Dataset DOI is added as metadata to the selected data objects.",
    style=info,
)

# --- Upload data files --- #

trg_path = "doc/data"

if inp_dv == "Demo":
    ## OPTION 1: LOCAL DOWNLOAD (for Demo installation)
    for item in data_objects_list:
        # Save data locally
        functions.save_df(item, trg_path, session)  # download object locally
        # Upload file(s)
        md = functions.deposit_df(api, dsPID, item.name, trg_path)
        print(md)
        # Update status of publication in iRODS from 'processed' to 'deposited'
        functions.save_md(item, atr_publish, "deposited", op="set")
        # Update timestamp
        functions.save_md(
            item, "dv.publication.timestamp", datetime.datetime.now(), op="set"
        )
else:
    ## OPTION 2: DIRECT UPLOAD (for RDR and RDR-pilot)
    for item in data_objects_list:
        objChecksum, objMimetype, objSize = functions.get_object_info(item)
        fileURL, storageID = functions.get_du_url(
            ds.baseURL, dsPID, objSize, header_key
        )
        du_step2 = functions.put_in_s3(item, fileURL, header_ct)
        md_dict = functions.create_du_md(storageID, item.name, objMimetype, objChecksum)
        du_step3 = functions.post_to_ds(md_dict, ds.baseURL, dsPID, header_key)
        # Update status of publication in iRODS from 'processed' to 'deposited'
        functions.save_md(item, atr_publish, "deposited", op="set")
        # Update timestamp
        functions.save_md(
            item, "dv.publication.timestamp", datetime.datetime.now(), op="set"
        )
        functions.save_md(
            item,
            "dv.df.storageIdentifier",
            storageID,
            op="add",
        )  # TO DO: for the metadata that are added and not set, make a repeatable composite field to group them together


# # Extract relevant datafile metadata - TO DO;
# df_id = functions.extract_atr(f"{md}", "id")

# # Add metadata in iRODS
# functions.save_md(
#     f"{objPath[i]}/{objName[i]}", "dv.df.id", df_id, session, op="set"
# )


c.print(
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
