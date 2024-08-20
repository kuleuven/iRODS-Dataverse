import os
import json
import argparse


def parse_mango_metadata(schema_path, data_object, schema_prefix="mgs"):
    if not os.path.exists(schema_path):
        raise FileNotFoundError
    schema = read_schema(schema_path, schema_prefix)
    return schema.extract(data_object)


def read_schema(schema_path, schema_prefix="mgs"):
    from mango_mdschema import Schema

    return Schema(schema_path, prefix=schema_prefix)


def parse_json_metadata(schema_path, dictionary, schema_prefix="mgs"):
    schema = read_schema(schema_path, schema_prefix)
    return schema.validate(dictionary)


def extract_template(path):
    if not os.path.exists(path):
        raise FileNotFoundError
    with open(path) as f:
        template = json.load(f)
    return template


def fill_in_template(template, avus):
    fields = template["datasetVersion"]["metadataBlocks"]["citation"]["fields"]
    new_fields = [update_template(field, avus) for field in fields]
    template["datasetVersion"]["metadataBlocks"]["citation"]["fields"] = new_fields


def return_dict(value, fromAvu):
    return {k: update_template(value[k], fromAvu) for k in value.keys()}


def update_template(field, avus_as_json):
    typeName = field["typeName"]
    value = field["value"]
    fromAvu = avus_as_json[typeName]
    typeClass = field["typeClass"]
    if typeClass != "compound":
        field["value"] = fromAvu
    elif type(value) == list:
        if type(fromAvu) != list:
            fromAvu = [fromAvu]
        field["value"] = [return_dict(x, y) for x, y in zip(value, fromAvu)]
    else:
        field["value"] = return_dict(value, fromAvu)
    return field


if __name__ == "__main__":
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
