import os
import json
import argparse


def parse_mango_metadata(schema_path, data_object, schema_prefix="mgs"):
    """Parse AVUs from ManGO metadata schema.

    Args:
        schema_path (str): Path to a JSON of a ManGO schema.
        data_object (irods.DataObject): Data object to extract the metadata from.
        schema_prefix (str, optional): Prefix used in the namespacing of the schema metadata. Defaults to "mgs".

    Raises:
        FileNotFoundError: If the schema is not found in the path provided.

    Returns:
        dict: Parsed and validated metadata in (nested) dictionary format without namespacing.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError
    schema = read_schema(schema_path, schema_prefix)
    return schema.extract(data_object)


def read_schema(schema_path, schema_prefix="mgs"):
    """Read schema from file

    This is an isolated function just so the `mango_mdschema` package is only
    imported when needed and it can be used both for reading metadata from an
    arbitrary dictionary and for extracting from an iRODS data object.

    Args:
        schema_path (str): Path to a JSON of a ManGO schema.
        schema_prefix (str, optional): Prefix used in the namespacing of the schema metadata. Defaults to "mgs".

    Returns:
        mango_mdschema.Schema: Representation of the schema, for validation and extraction of metadata.
    """
    from mango_mdschema import Schema

    return Schema(schema_path, prefix=schema_prefix)


def parse_json_metadata(schema_path, dictionary):
    """Parse metadata from a dictionary

    Args:
        schema_path (str): Path to a JSON of a ManGO schema.
        dictionary (dict): Metadata without namespacing but matching a schema specification.

    Returns:
        dict: Validated metadata
    """
    schema = read_schema(schema_path)
    return schema.validate(dictionary)


def extract_template(path):
    """Read Dataverse template from path

    Args:
        path (str): Path to the JSON of the Dataverse template whose values need to be filled in
          with actual metadata.

    Raises:
        FileNotFoundError: When the path to the template is not found.

    Returns:
        dict: Contents of the template, to be filled in with actual metadata.
    """
    if not os.path.exists(path):
        raise FileNotFoundError
    with open(path) as f:
        template = json.load(f)
    return template


def fill_in_template(template, avus):
    """Fill in Dataverse template with metadata

    This function does not return anything but just modifies the template itself (the dict).

    Args:
        template (dict): Contents of the template, e.g. output of `extract_template()`.`
        avus (dict): Dictionary with metadata, with keys matching the required fields in the template.
    """
    fields = template["datasetVersion"]["metadataBlocks"]["citation"]["fields"]
    new_fields = [update_template(field, avus) for field in fields]
    template["datasetVersion"]["metadataBlocks"]["citation"]["fields"] = [
        field for field in new_fields if fields is not None
    ]


def return_dict(value, fromAvu):
    """Make `update_template()` recursive

    Args:
        value (dict): Contents of the "value" attribute of a field in the Dataverse template.
        fromAvu (dict): Key-value pairs to fill in this subset of the template

    Returns:
        dict: Key-value pairs with the matching between a nested field and its corresponding AVUs.
    """
    return {k: update_template(value[k], fromAvu) for k in value.keys()}


def update_template(field, avus_as_json):
    """Match a template field to the corresponding metadata

    `return_dict()` is used to apply `update_template()` to nested subsets.

    Args:
        field (dict): Field in the Dataverse template (part of the "fields" array).
        avus_as_json (dict): Key-value pairs with metadata, maybe nested

    Returns:
        dict: Filled in field to update the template with.
    """

    typeName = field["typeName"]
    value = field["value"]
    # get the value from avu based on typename
    if typeName not in avus_as_json:
        return None
    fromAvu = avus_as_json[typeName]
    typeClass = field["typeClass"]
    # put single value in list if multiple is true
    if field["typeClass"] == "controlledVocabulary" and field["multiple"] == True:
        if type(fromAvu) != list:
            fromAvu = [fromAvu]
    if typeClass != "compound":
        field["value"] = fromAvu
    elif type(value) == list:
        if type(fromAvu) != list:
            fromAvu = [fromAvu]
        field["value"] = [return_dict(x, y) for x, y in zip(value, fromAvu)]
    else:
        field["value"] = return_dict(value, fromAvu)
    return field


def get_template(path_to_template, metadata):
    """Turn a metadata dictionary into the configured Dataverse filled-in template

    Parameters
    ----------
    path_to_template : str
        The path to the original template
    metadata : dict
        A simplified dictionary with metadata

    Returns
    -------
    template: dict
        A complete template as dictionary
    """
    with open(path_to_template) as f:
        template = json.load(f)
    # fill in template
    fill_in_template(template, metadata)
    return template


if __name__ == "__main__":
    """This is only for testing and demo'ing. The idea is that this is called as a module and the functions used as part
    of some automated script.
    """
    parser = argparse.ArgumentParser(
        description="Parse iRODS Metadata for Dataverse submission."
    )
    parser.add_argument(
        "dataverse_template", help="Path to the metadata template to send to Dataverse."
    )
    parser.add_argument("output_path", help="Path to store the final file")
    parser.add_argument(
        "-j",
        "--local_json",
        help="Path to a JSON file with the metadata. A schema may be used to validate.",
    )
    parser.add_argument(
        "-p",
        "--logical_path",
        help="Path to an object in iRODS with the metadata. Ignored if a local JSON path is provided. Use a schema to convert.",
    )
    parser.add_argument(
        "-s",
        "--schema",
        help="Path to a ManGO schema. Necessary if a logical path is provided. If used, the mango-mdschema package must be installed.",
    )

    args = parser.parse_args()

    if not os.path.exists(args.dataverse_template):
        raise FileNotFoundError
    with open(args.dataverse_template) as f:
        template = json.load(f)

    if args.local_json is not None:
        if not os.path.exists(args.local_json):
            raise FileNotFoundError
        with open(args.local_json) as f:
            metadata = json.load(f)
            if args.schema is not None:
                metadata = parse_json_metadata(args.schema, metadata)
    elif args.logical_path is not None:
        if args.schema is None:
            raise Exception("Please provide a ManGO schema to parse the AVUs.")
        from irods.session import iRODSSession

        try:
            env_file = os.environ["IRODS_ENVIRONMENT_FILE"]
        except KeyError:
            env_file = os.path.expanduser("~/.irods/irods_environment.json")

        ssl_settings = {}
        with iRODSSession(irods_env_file=env_file, **ssl_settings) as session:
            obj = session.data_objects.get(args.logical_path)
            metadata = parse_mango_metadata(args.schema, obj)
    else:
        raise Exception("Provide either a logical path or a local JSON.")
    fill_in_template(template, metadata)
    with open(args.output_path, "w") as f:
        json.dump(template, f, indent=4)
