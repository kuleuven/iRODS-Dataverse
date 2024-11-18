# iRODS-Dataverse
This is an implementation for programmatic publication of data from iRODS into a Dataverse installation.

## Prerequisites 
1) Being an iRODS user with data in an iRODS zone.
2) Authenticate to Dataverse:
- Sign up with individual account
- Get the API Token which is valid for a certain amount of time (demo: one year)
3) Run the scripts with internet access


## Set up the virtual environment
```
$ python -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

When finished, deactivate the virtual environment
```
$ deactivate
```

## User script
After the virtual environment is activated run:
```
$ python src/userScript.py
```

Visual overview of the pipeline options:

<img src="./doc/img/20241108_pipeline_options.png" alt="overview-pipeline-options" style="height: 794px; width: 728px;"/>


## avu2json: Convert iRODS AVU or normal dictionary to Dataverse metadata

The JSON to send to Dataverse metadata is quite complex (e.g. [template_Demo.json](./doc/metadata/template_Demo.json)), so we would like our users to be able to input the metadata of the dataset more easily.
The ["avu2json" module](./src/avu2json.py) can handle either a JSON file with a simple dictionary (such as [rdr_metadata.json](./doc/metadata/rdr_metadata.json)) or ManGO schema metadata on a data object (coming soon: a collection?).
If the metadata comes from a simple dictionary, it is possible to validate it with a schema. If it comes from a data object instead, it must be.
Therefore, if the same dictionary comes from a different source, it can also be used without ManGO schema validation.

To use it from the command line, start from this directory, create a virtual environment and install the necessary packages (`mango-mdschema` for ManGO schema validation and `python-irodsclient` if we need to collect metadata from iRODS). The script has two positional arguments: the path to the template for Dataverse and a path to store the output. Then, it has three optional arguments:

- `-p` or `--logical_path` is the path of an iRODS Data object
- `-j` or `--local_json` is the path to a JSON with the metadata, such as [rdr_metadata.json](./doc/metadata/rdr_metadata.json)
- `-s` or `--schema` is the path to a [ManGO Schema](./doc/metadata/mango2dv-rdr-1.0.0-published.json)

At least one of `--logical_path` or `--local_json` are necessary; the `--schema` is necessary if the `--logical_path` is provided instead of the `--local_json`.

You may test this by running:

```sh
cd src
python -m avu2json ../doc/metadata/template_RDR.json RDR_output.json -j ../doc/metadata/rdr_metadata.json -s ../doc/metadata/mango2dv-rdr-1.0.0-published.json
```

Skip the `-s ../doc/metadata/mango2dv-rdr-1.0.0-published.json` if you don't want the validation :)

Within a script that is connected to Dataverse, you may call the module itself instead:

```python
import avu2json
import json
path_to_metadata = "../doc/metadata/rdr_metadata.json"
path_to_template = "../doc/metadata/template_RDR.json"

with open(path_to_metadata) as f:
    metadata = json.load(f)

# skip this next part if you don't want validation
path_to_schema = "../doc/metadata/mango2dv-rdr-1.0.0-published.json"
metadata = avu2json.parse_json_metadata(path_to_schema, metadata)

with open(path_to_template) as f:
    template = json.load(f)
avu2json.fill_in_template(template, metadata)
# this modifies the "template" and it can be sent directly to Dataverse
```