# iRODS-Dataverse
This is an implementation for programmatically creating a draft dataset publication from data stored in iRODS into a configured Dataverse installation. 
The final submission of the dataset takes place in the Dataverse installation itself, since additional steps may be required (e.g. submit dataset to review).

## Prerequisites 
1) Being an iRODS user with data in an iRODS zone.
2) Have a Dataverse account, in one of the configured installations (currently [Demo](https://demo.dataverse.org/), [RDR](https://rdr.kuleuven.be/) or [RDR-pilot](https://www.rdm.libis.kuleuven.be/)).
    - Sign up with individual account. 
    - Get the API Token which is valid for a certain amount of time (e.g. in Demo the API Token is valid for one year)
3) Set up the virtual environment:

    ```sh
    python -m venv venv
    source venv/bin/activate
    pip install irods2dataverse
    ```

    When the process is finished, deactivate the virtual environment:

    ```sh
    deactivate
    ```

## User script

After installing the package in the virtual environment start the process:

```sh
python -m irods2dataverse.userScript
```

This will trigger an interactive terminal that will take you through the following steps:

1. Authenticate to iRODS. For KU Leuven users this happens automatically by reading your local `irods_environment.json`.

2. Identify the data object(s) to send to Dataverse. There are two possibilities:
* Tag the data objects with metadata attribute `dv.publication` and value `initiated`.
* Provide the absolute path(s) of the data object(s) to be sent to Dataverse. The input paths refer either to a single data object `/zone/home/collection/file`, or a list of objects `["/zone/home/collection/file_1", "/zone/home/collection/file_2"]`.

3. Identify the target Dataverse installation. The script goes through the selected data object(s)
and retrieves the metadata field `dv.installation`. If it is not valid or missing, input it from a selection.

4. Authenticate to the Dataverse installation. The script will ask you to input your API Token.

5. Gather the metadata needed to create a draft in the selected Dataverse installation. There are three possibilities:

- (For ManGO users) Use a [metadata schema](./src/resources/mango2dv-rdr-1.0.0-published.json): The schema can be used to add
the metadata to any object of the list. One object suffices. 
- Provide the metadata via the CLI: The script asks to provide the value for each required metadata field. 
- Fill in a JSON and provide the path to the file: Copy the metadata template of the selected Dataverse installation, e.g. [Demo template](./src/resources/template_Demo.json) and fill it in. Alternatively, create a shorter JSON file with the minimal metadata. For example, the text below shows the contents of the short JSON file, with metadata for the Demo installation:

    ```json
    {
        "author": {
            "authorAffiliation": "My university",
            "authorName": "Surname, Given Name"
        },
        "datasetContact": {
            "datasetContactEmail": "username@domain.edu",
            "datasetContactName": "Surname, Given Name"
        },
        "dsDescription": [
            {
                "dsDescriptionValue": "This is the first dataset I send from iRODS"
            }
        ],
        "subject": [
            "Demo Only"
        ],
        "title": "My dataset"
    }
    ```

    For RDR, the short JSON file would have, for example, the following contents:

    ```json
    {
        "access": {
            "accessRights": "open",
            "dateAvailable": "",
            "legitimateOptout": "other"
        },
        "author": [
            {
                "authorAffiliation": "My university",
                "authorName": "Surname, Given Name"
            }
        ],
        "datasetContact": [
            {
                "datasetContactEmail": "username@domain.edu",
                "datasetContactName": "Surname, Given Name"
            }
        ],
        "dsDescription": [
            {
                "dsDescriptionValue": "This is the first dataset I send from iRODS"
            }
        ],
        "keyword": [
            {
                "keywordValue": "required-keyword"
            }
        ],
        "technicalFormat": "json",
        "title": "My dataset"
    }
    ```

    To work with the short JSON file, copy the text above and adapt the values into a text file.

    **Note:** For the RDR long template, when the _access rights_ are open, omit the fields regarding _available date_ and _legitimate opt-out_.

6. The script validates the metadata. 

7. The script deposits the draft with its metadata in the selected Dataverse installation. The data objects are directly uploaded to S3 without download.

8. The script updates the metadata of the data objects send to Dataverse with the DOI provided by Dataverse.


## Configuring another Dataverse installation

If you want to configure this script to work with other Dataverse installations,
look at [the custom classes](./src/irods2dataverse/customClass.py) or [contact us](mailto:rdm-icts@kuleuven.be).
