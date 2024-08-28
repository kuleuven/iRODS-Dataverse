import functions
import maskpass
import datetime
from os.path import expanduser

# ---- define custom colors (Octal ANSI sequences for colors ; https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797#8-16-colors) => put in class?

esccolor = "\033[39m"  # color for the instructions, also the default color.
actioncolor = "\033[33m"  # color for information on the actions in iRODS.
infocolor = "\033[36m"  # color for messages related to the process, other than actions in iRODS.
warningcolor = "\x1b[1;31m"


#-------------------------------------------------------------------------#
# # To drive the process based on metadata, go to your selected zone and
#  add the following metadata to at least one data object:
# A: dv.publication   V: initiated
# A: dv.installation  V: Demo
#--------------------------------------------------------------------------#

#  --- Provide the iRODS environment file to authenticate in a specific autzone ---#

print("Authenticate to iRODS zone")
home_dir = expanduser("~")
session = functions.authenticate_iRODS(f"{home_dir}/.irods/irods_environment.json") #only worked after providing the full path
if session: 
    print(f"{infocolor}You are now authenticated to iRODS{esccolor}")
else:
    print("You are not authenticated to Irods")


# --- Select Data: if there is no metadata specifying the obcject that needs to be published, ask user to provide the path --- #

print("Select data in iRODS, via attached metadata in iRODS or via iRODS paths as typed input")
atr_publish = "dv.publication"   
val = "initiated"
qdata = functions.query_data(atr_publish, val, session)  #look for data based on A = dv.publication & value = initiated
ldt = qdata   #returns a list
if len(ldt) == 0:
    print(
        f"{infocolor}No metadata with attribute <{atr_publish}> and value <{val}> are found.{esccolor}"
    )
    inp_dt = []
    add = True
    while add:
        print(
            "Provide the full iRODS path and name of the data object to be published in one of the configured Dataverse installations" 
            #removed "a string with" because input() always returns a string 
        )
        inp_i = input()
        #functions.get_data_object(session, inp_i)
        inp_dt.append(inp_i) #add metadata with dedicated attribute and value in this data object
        if (functions.save_md(inp_i, atr_publish, val, session)):
            print(f"{actioncolor}Metadata with attribute <{atr_publish}> and value <{val}> are added in the selected data object.{esccolor}")
        else: 
            print(f"{warningcolor}The path of the data object is not correct. Please provide a correct path.{esccolor}")
        print("Add more objects? y/n")
        cont = input()
        if cont == "n":
            add = False
else:
    print(
        f"{infocolor}Metadata with attribute <{atr_publish}> and value <{val}> are found in iRODS.{esccolor}"
    )
    inp_dt = ldt
print(
    f"{infocolor} The following objects are selected for publication:\n <{inp_dt}>.{esccolor}"
)

# --- Process input data list (split iRODS path and filename) <<<< CHECK

objInfo = functions.split_obj(inp_dt)
objPath = objInfo[0]
objName = objInfo[1]
print(objPath)
print(objInfo[0])

for i in range(len(objName)):
    # Update status of publication in iRODS from 'initiated' to 'processed'
    functions.save_md(f"{objPath[i]}/{objName[i]}", atr_publish, "processed", session)
    # Dataset status timestamp
    functions.save_md(
        f"{objPath[i]}/{objName[i]}",
        "dv.publication.timestamp",
        datetime.datetime.now(),
        session,
    )
print(
    f"{infocolor}Metadata attribute <{atr_publish}> is updated to <processed> for the selected objects.{esccolor}"
)

# --- Select Dataverse: if there is no object metadata specifying the Dataverse installation, ask for user input

print(
    "Select one of the configured Dataverse installations, via attached metadata in iRODS or via typed input"
)
atr_dv = "dv.installation"
ldv = functions.query_dv(atr_dv, objPath, objName, session)
if len(ldv) == 0:
    print(f"{infocolor}The selected objects have no attribute <{atr_dv}>.{esccolor}")
    print(
        "Specify the configured Dataverse installation to publish the data.\nType RDR or Demo"
    )
    inp_dv = input()
    for item in ldt:
        functions.save_md(item, atr_dv, inp_dv, session)
    print(
        f"{actioncolor}Metadata with attribute <{atr_dv}> and value <{inp_dv}> are added in the selected data objects.{esccolor}"
    )
else:
    inp_dv = ldv[0]
    print(
        f"{infocolor}Metadata with attribute <{atr_dv}> and value <{inp_dv}> for the selected data objects are found in iRODS.{esccolor}"
    )

# --- Set-up for the selected Dataverse installation & ask for api-token --- #

print(
    f"Provide your Token for <{inp_dv}> Dataverse installation. Your Token will be encrypted and saved securely for future reference until expiration [TO DO <<< CHECK IF OKAY]."
)
token = ""
while len(token) <= 0: 
        token = maskpass.askpass(prompt="", mask="*")
else: 
    resp = functions.setup(inp_dv, token)  # this function also validates that the selected Dataverse installations is configured.

# --- Initiate a dataset in the selected Dataverse installation ---#

ds = functions.initiate_ds(inp_dv)
input()  # Pause until the user provides the metadata >>>>> TO DO: CHANGE
# >>>>> TO DO: provide a path for the metadata ; use data object metadata: A: dv.mdpath V: /set/home/datateam_set/iRODS2DV/md_ds.json
# >>>>> TO DO: modify the following while loop

# Validate metadata
# md = resp[0][1]
# print(
#     md
# )  # this is the local path to the json metadata template (doc/metadata/md_Demo.json) - put the md in iRODS

md = f"{home_dir}/iRODS-Dataverse/doc/metadata/mdDataset_Demo.json"

vmd = functions.validate_md(ds, md)
while not (vmd):
    print(
        f"The metadata are not validated, modify <{md}>, save and hit enter to continue."
    )
    input()
    vmd = functions.validate_md(ds, md)
print("The metadata are validated, the process continues.")

# ---  Deposit draft in selected Dataverse installation

ds_md = functions.deposit_ds(resp[1][1], inp_dv, ds)
print(f"{infocolor}The Dataset publication metadata are: {ds_md}{esccolor}")


# --- Add dataset metadata in iRODS --- #

for i in range(len(objName)):
    # Update status of publication in iRODS from 'processed' to 'deposited'
    functions.save_md(f"{objPath[i]}/{objName[i]}", atr_publish, "deposited", session)
    # Dataset status timestamp
    functions.save_md(
        f"{objPath[i]}/{objName[i]}",
        "dv.publication.timestamp",
        datetime.datetime.now(),
        session,
    )
    # Dataset DOI
    functions.save_md(f"{objPath[i]}/{objName[i]}", "dv.ds.DOI", ds_md[1], session)
    # Dataset PURL
    functions.save_md(f"{objPath[i]}/{objName[i]}", "dv.ds.PURL", ds_md[3], session)
print(
    f"{infocolor}Metadata attribute <{atr_publish}> is updated to <deposited> for the selected data objects.{esccolor}"
)
print(
    f"{infocolor}The Dataset DOI and PURL are added as metadata to the selected data objects.{esccolor}"
)

# ---  Save data locally <<<<< CHECK alternatives for the user script --- #

trg_path = f"{home_dir}/iRODS-Dataverse/doc/data"
functions.save_df(objPath, objName, trg_path, session)

# --- Upload file(s): Include an option that if there are multiple objects either use a loop or use a python module for parallel upload. ---#

df_md = functions.deposit_df(resp[1][1], ds_md[1], objName, trg_path)


# # Extract PID of each file(s) ==> This is the same as the Dataset DOI, check if there is file specific metadata
# df_PID = functions.extract_atr(df_md[1][0], "pid")
# print(df_PID)

# # Add datafile metadata in iRODS
# for i in range(len(objName)):
#     # Datafile DOI
#     functions.save_md(f"{objPath[i]}/{objName[i]}", "dv.df.DOI", df_PID[i], session)
#     print(
#         f"{infocolor}The Datafile DOI is added as metadata to the selected data object.{esccolor}"
#     )


# Additional metadata could be extracted from the filled-in Dataverse metadata template (e.g. author information)

# Clean-up
session.cleanup()

# # Publication/Send for review # #
# The current agreement is to send for publication via the Dataverse UI.
# This is because different procedures may apply in each Dataverse installation.
# To update the status of the publication (atr_publish) from deposited to "published", we need to check the situation in Dataverse.
# There is potential way to see if the DOI of the dataset and datafile(s) are published.
# We have talked about running checksums to see if the publication data are altered outside iRODS.
