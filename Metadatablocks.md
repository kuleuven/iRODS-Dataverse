
## MetadataBlocks.py : request metadatablocks from dataverse installation


Uses: request all metadatablocks from dataverse installation & create a template to upload with required fields


#### About the datastructure:

* **typeClass:**
  * "primitive":  value is a string
  * "compound":  value is a dictionary with key: value pairs where the key is another field and value is the value, typeclass, multiple, typeName


* **multiple:** 
  * true : multiple value are possible we put our dictionary/dictionaries in a list
  * false:  multiple value are not possible, no list

* **typeName:**
  * name of the field


#### required parameters:
* name for dataverse installation: the following installations are available: demo, RDR, RDR-Pilot, Harvard, DANS
* api token for chosen dataverse installation

#### optional parameters:

Extra_fields = list of possible extra fields that are added to the metadata template



## Methods:

*  set_dv_url():   
this method checks the dataverse installation based on the user input and sets the dv_url attribute

*  check_extra_fields():  
 this method checks the extra fields requested by the user 

*  get_mdblocks():  
 gets metadatablocks from dataverse

*  remove_childfields():  
removes the fields from the top level that already exist as childfields of a compound field
        
* write_clean_mdblocks():  
 gets metadatablocks from api, cleans them & write to file

* clean_mdblocks():  
gets metadatablocks from api and cleans them

* get_datasetSchema():  
this method gets the schema and stores it as an attribute schema

* write_schema(self):  
 this method write the schema to a json file

* get_controlled_vocabularies():  
This function gets all the controlled vocabularies 

* create_field(self, value, typeClass, compound=None):   
This function makes a copy of the template (field_info) and fills in the necessary 
information based on the provided parameters: either compound or not compound


*  add_required(self, all_blocks, block):  
function to add required fields

* create_json_to_upload():  
This function creates & writes the json 

* find_controlled_vocabulary():  

* fill_in_md_template():  
prompts user to fill in values for md upload form


## basic example:

```python
#import library

from MetadataBlocks import MetadataBlocks

#create instance of object: 

mdb = MetadataBlocks(
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


#create an empty template 
mdb.create_json_to_upload()

#prompt user to fill in template & save
mdb.fill_in_md_template()

#set md as your filenmae
md = mdb.file_name

