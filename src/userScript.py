import functions
import maskpass

# Provide the iRODS environment file to authenticate in a specific zone
session = functions.authenticate_iRODS("~/.irods/irods_environment.json")

# Select Data: if there is no metadata specifying the object that needs to be published, ask user to provide the path
qdata = functions.query_data("dv.publication", "initiated", session)
ldt = qdata
if len(ldt) == 0:
    inp_dt = []
    add = True
    while add:
        print(
            "Provide a string with the full iRODS path and name of the data object to be published in one of the configured Dataverse installations"
        )
        inp_i = input()
        inp_dt.append(inp_i)
        print("Add more objects? y/n")
        cont = input()
        if cont == "n":
            add = False
else:
    inp_dt = ldt


# Select Dataverse: if there is no object metadata specifying the Dataverse installation, ask for user input
ldv = functions.query_dv("dv.installation", ldt, session)
if len(ldv) == 0:
    print(
        "Select one of the configured Dataverse installations to publish the data.\nType RDR or Demo"
    )
    inp_dv = input()
    # Save input as iRODS object metadata
    for item in ldt:
        print(item)
        functions.save_md(item, "dv.installation", inp_dv, session)
else:
    inp_dv = ldv[0]

# Set-up for the selected Dataverse installation
print(
    f"Provide your Token for Dataverse {inp_dv} installation. Your Token will be encrypted and saved securely for future reference until expiration."
)
token = maskpass.askpass(prompt="", mask="*")
resp = functions.setup(inp_dv, token)

# Initiate a dataset in the selected Dataverse installation
ds = functions.initiate_ds(inp_dv)
input()  # Pause until the user provides the metadata

# Validate metadata
md = resp[0][1]
vmd = functions.validate_md(ds, md)
while not (vmd):
    print(
        f"The metadata are not validated, modify {md}, save and hit enter to continue."
    )
    input()
    vmd = functions.validate_md(ds, md)
print("The metadata are validated, the process continues.")


# Deposit draft in selected Dataverse installation
ds_md = functions.deposit_ds(resp[1][1], inp_dv, ds)
print(f"The Dataset publication metadata are: {ds_md}")

# TO DO:
# 1) Upload file(s)
# 2) Add metadata (PURL, DOI) in iRODS
# 3) Additional testing and logic


# Clean-up
session.cleanup()
