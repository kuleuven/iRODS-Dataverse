# Convert iRODS AVU or normal dictionary to Dataverse metadata

The JSON to send to Dataverse metadata is quite complex (see the files in the data subdirectory here), so we would like our users to be able to input the metadata of the dataset more easily.
The script "avu2json" can handle either a JSON file with a simple dictionary (such as [rdr_metadata.json](data/rdr_metadata.json)) or ManGO schema metadata on a data object (coming soon: a collection?).
If the metadata comes from a simple dictionary, it is possible to validate it with a schema. If it comes from a data object instead, it must be.
Therefore, if the same dictionary comes from a different source, it can also be used without ManGO schema validation.

To use it from the command line, start from this directory, create a virtual environment and install the necessary packages (`mango-mdschema` for ManGO schema validation and `python-irodsclient` if we need to collect metadata from iRODS). The script has two positional arguments: the path to the template for Dataverse and a path to store the output. Then, it has three optional arguments:

- `-p` or `--logical_path` is the path of an iRODS Data object
- `-j` or `--local_json` is the path to a JSON with the metadata, such as [rdr_metadata.json](data/rdr_metadata.json)
- `-s` or `--schema` is the path to a [ManGO Schema](data/mango2dv-rdr-1.0.0-published.json)

At least one of `--logical_path` or `--local_json` are necessary; the `--schema` is necessary if the `--logical_path` is provided instead of the `--local_json`.

You may test this by running:

```sh
python -m avu2json data/template_RDR.json output/RDR_output.json -j data/rdr_metadata.json -s data/mango2dv-rdr-1.0.0-published.json
```

Skip the `-s data/mango2dv-rdr-1.0.0-published.json` if you don't want the validation :)

Within a script that is connected to Dataverse, you may call the module itself instead:

```python
import avu2json
import json
path_to_metadata = "data/rdr_metadata.json"
path_to_template = "data/template_RDR.json"

with open(path_to_metadata) as f:
    metadata = json.load(f)

# skip this next part if you don't want validation
path_to_schema = "data/mango2dv-rdr-1.0.0-published.json"
metadata = avu2json.parse_json_metadata(path_to_schema, metadata)

with open(path_to_template) as f:
    template = json.load(f)
avu2json.fill_in_template(template, metadata)
# this modifies the "template" and it can be sent directly to Dataverse
```