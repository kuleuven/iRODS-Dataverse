
## metadatablocks.py : request metadatablocks from a Dataverse installation


Usage: Request all metadatablocks from a Dataverse installation and create a template to upload with required fields


#### About the data structure:

* **typeClass:**
  * "primitive":  value is a string
  * "compound":  value is a dictionary with key: value pairs where the key is another field and value is the value, typeclass, multiple, typeName


* **multiple:** 
  * true: multiple value are possible we put our dictionary/dictionaries in a list
  * false:  multiple value are not possible, no list

* **typeName:**
  * name of the field


#### required parameters:
* name of a Dataverse installation: the following installations are available: Demo, RDR, RDR-Pilot
* api token for the chosen Dataverse installation

#### optional parameters:

Extra_fields = list of possible extra fields that are added to the metadata template



## Methods:

*  set_dv_url():   
This method checks the Dataverse installation based on the user input and sets the dv_url attribute

*  check_extra_fields():  
 This method checks the extra fields requested by the user 

*  get_mdblocks():  
 This method gets metadatablocks from Dataverse

*  remove_childfields():  
This method removes the fields from the top level that already exist as childfields of a compound field
        
* write_clean_mdblocks():  
This method gets metadatablocks from api, cleans them & writes to file

* clean_mdblocks():  
This method gets metadatablocks from api and cleans them

* get_controlled_vocabularies():  
This method gets all the controlled vocabularies 

* create_field(self, value, typeClass, compound=None):   
This method makes a copy of the template (field_info) and fills in the necessary 
information based on the provided parameters: either compound or not compound

*  add_required(self, all_blocks, block):  
This method adds required fields

* create_json_to_upload():  
This method creates & writes the json 

* find_controlled_vocabulary(name):
This method takes the typeName of a field and returns a list of the possible
values for the controlled vocabulary 

For example

```python
blocks.find_controlled_vocabulary("subject")
```

* fill_in_md_template():  
This method prompts user to fill in values for the metadata upload form for Dataverse


## example 1: request required fields plus a list of non-required fields

```python
# import library

from irods2dataverse import metadatablocks

# create instance of object: 

mdb = metadatablocks.Metadatablocks(
    "Demo",
    api_token,
    [
        "authorAffiliation",
        "departmentFaculty",
        "datasetContactName",
        "datasetContactAffiliation",
        "dateAvailable",
        "legitimateOptout",
    ],
)


# create an empty template 
mdb.create_json_to_upload()

# prompt user to fill in template & save
mdb.fill_in_md_template()

# set md as your filename
md = mdb.file_name

```

## example 2: request required fields only

```python


mdb = metadatablocks.Metadatablocks(
    "Demo",
    api_token,
)

# write all the possible metadatablocks to file
mdb.write_clean_mdblocks():


```