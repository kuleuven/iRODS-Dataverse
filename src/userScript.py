import functions
import maskpass
import datetime
from os.path import expanduser

# ---- define custom colors (Octal ANSI sequences for colors ; https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797#8-16-colors) 

# Test with 2 files /set/home/datateam_set/iRODS2DV/20240718_demo
# Use DVUploader and Include an option on which upload method should be chosen.

# Dataverse installations are pre-configured, using customClass.py and customization.ini.
# This script implements the perspective where the individual data objects destined for publication are either annotated with metadata or their path is provided.
# Another perspective that could be explored is the case where the dataset is all in a pre-specified iRODS collection and the structure is mirrored in Dataverse.

# define custom ascii octal colors => TO DO: use rich instead
esccolor = "\033[39m"  # color for the instructions, also the default color.
actioncolor = "\033[33m"  # color for information on the actions in iRODS.
infocolor = "\033[36m"  # color for messages related to the process, other than actions in iRODS.
warningcolor = "\x1b[1;31m" #color to indicate that something is wrong

print("""
#--------------------------------------------------------------------------#
# To drive the process based on metadata, go to your selected zone and     #
#  add the following metadata to at least one data object:                 #
# A: dv.publication   V: initiated                                         #
# A: dv.installation  V: Demo                                              #
#--------------------------------------------------------------------------# 
""")

#--- set home directory -- # 

home = expanduser("~")

#  --- Provide the iRODS environment file to authenticate in a specific autzone ---#

print("Authenticate to iRODS zone")
session = functions.authenticate_iRODS(f"{home}/.irods/irods_environment.json") 
if session: 
    print(f"{infocolor}You are now authenticated to iRODS{esccolor}")
else:
    raise SystemExit  


# --- Select Data: if there is no metadata specifying the obcject that needs to be published,  ask user to provide the path --- #

print("Select data in iRODS, via attached metadata in iRODS or via iRODS paths as typed input")

atr_publish = "dv.publication"   
val = "initiated"
data_objects_list = functions.query_data(atr_publish, val, session)  #look for data based on A = dv.publication & value = initiated
if len(data_objects_list) == 0: #ldt = qdata   
    print(f"{infocolor}No metadata with attribute <{atr_publish}> and value <{val}> are found.{esccolor}")
    add = True
    while add:
        print("Provide the full iRODS path and name of the data object to be published in one of the configured Dataverse installations")
        inp_i = input()
        try: 
            obj = session.data_objects.get(inp_i)
            data_objects_list.append(obj)
            if (functions.save_md(inp_i, atr_publish, val, session, op="set")):
                print(f"{actioncolor}Metadata with attribute <{atr_publish}> and value <{val}> are added in the selected data object.{esccolor}")
            else: 
                print(f"{warningcolor}The path of the data object is not correct. Please provide a correct path.{esccolor}")
        except Exception as e: #change this to specific exception
            inp_i = "none"
        print("Add more objects? y/n")
        cont = input()
        if cont == "n":
            add = False
else:
    print(
        f"{infocolor}Metadata with attribute <{atr_publish}> and value <{val}> are found in iRODS.{esccolor}"
    )
    #inp_dt = ldt
print(
    f"{infocolor} The following objects are selected for publication:\n <{data_objects_list}>.{esccolor}"
)

""" irods data objects have method path & name !
# --- Process input data list (split iRODS path and filename) <<<< CHECK
objInfo = functions.split_obj(inp_dt)
objPath = objInfo[0]
objName = objInfo[1]
print(objPath)
print(objInfo[0])
"""

# --- update metadata in irods for from initiated to processed & add timestamp --- #

for item in data_objects_list:
    # Update status of publication in iRODS from 'initiated' to 'processed'
    functions.save_md(
        item.path, atr_publish, "processed", session, op="set"
    )
    # Dataset status timestamp
    functions.save_md(item.path,"dv.publication.timestamp",datetime.datetime.now(),session, op="set")

print(f"{infocolor}Metadata attribute <{atr_publish}> is updated to <processed> for the selected objects.{esccolor}")

# Select Dataverse: if there is no object metadata specifying the Dataverse installation, ask for user input
print(
    "Select one of the configured Dataverse installations, via attached metadata in iRODS or via typed input."
)
atr_dv = "dv.installation"
ldv = functions.query_dv(atr_dv, data_objects_list, session)
if len(ldv) == 0:
    print(f"{infocolor}The selected objects have no attribute <{atr_dv}>.{esccolor}")
    print("Specify the configured Dataverse installation to publish the data.\nType RDR or Demo")
    inp_dv = input()
    for item in data_objects_list:
        functions.save_md(item, atr_dv, inp_dv, op="set")
    print(f"{actioncolor}Metadata with attribute <{atr_dv}> and value <{inp_dv}> are added in the selected data objects.{esccolor}")
else:
    inp_dv = ldv[0]
    print(f"{infocolor}Metadata with attribute <{atr_dv}> and value <{inp_dv}> for the selected data objects are found in iRODS.{esccolor}")

# Set-up for the selected Dataverse installation
print(f"Provide your Token for <{inp_dv}> Dataverse installation.")
token = maskpass.askpass(prompt="", mask="*")
resp = functions.setup(
    inp_dv, token
)  # this function also validates that the selected Dataverse installations is configured.
ds = resp[2]

print(
    f"{infocolor}Provide the path for the filled-in Dataset metadata. The metadata should match the template <{ds.metadataTemplate}> [PLACEHOLDER - see avu2json]\n The filled-in template for Demo is now at doc/metadata/mdDataset_Demo.json and for RDR at doc/metadata/mdDataset_RDR.json{esccolor}"
)
md = input()

# Validate metadata
vmd = functions.validate_md(resp[2], md)
while not (vmd):
    print(
        f"{infocolor}The metadata are not validated, modify <{md}>, save and hit enter to continue [PLACEHOLDER - see avu2json].{esccolor}"
    )
    input()
    vmd = functions.validate_md(resp[2], md)
print(f"{infocolor}The metadata are validated, the process continues.{esccolor}")

# Deposit draft in selected Dataverse installation
ds_md = functions.deposit_ds(resp[1][1], inp_dv, resp[2])
print(f"{infocolor}The Dataset publication metadata are: {ds_md}{esccolor}")


for item in data_objects_list:
    # Dataset DOI
    functions.save_md(item.path, "dv.ds.DOI", ds_md[1], session, op="add")
    # Dataset PURL
    functions.save_md(item.path, "dv.ds.PURL", ds_md[3], session, op="set")
print(
    f"{infocolor}Metadata attribute <{atr_publish}> is updated to <deposited> for the selected data objects.{esccolor}"
)
print(
    f"{infocolor}The Dataset DOI and PURL are added as metadata to the selected data objects.{esccolor}"
)

# ---  Save data locally <<<<< CHECK alternatives for the user script --- #

trg_path = f"{home}/iRODS-Dataverse/doc/data"
functions.save_df(data_objects_list, trg_path, session)

# --- Upload file(s): Include an option that if there are multiple objects either use a loop or use a python module for parallel upload. ---#

df_md = functions.deposit_df(resp[1][1], ds_md[1], data_objects_list, trg_path)


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

# Next step - 1: Publication / Send for review via Dataverse installation UI
# The current agreement is to send for publication via the Dataverse UI.
# This is because different procedures may apply in each Dataverse installation.

# Next step - 2: Update the metadata in iRODS
# From the iRODS side, to update the status of the publication (atr_publish) from deposited to "published", we need to check the situation in Dataverse.
# With periodic checks, query for the DOI of the dataset and check in the metadata if the dataset is published.
# We have talked about running checksums to see if the publication data are altered outside iRODS.

# Clean-up iRODS session
session.cleanup()
