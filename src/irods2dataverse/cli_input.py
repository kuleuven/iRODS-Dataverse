import json
import ast
from rich.prompt import Prompt
from pathlib import Path
import re
from datetime import datetime


def is_list(input):
    """Checks if user input represents a python list.

    Parameters
    ----------
    input (str): User input typed in CLI

    Returns
    -------
    bool: Returning value
    """
    try:
        return isinstance(ast.literal_eval(input), list)
    except SyntaxError:
        return False


def to_list(input):
    """Converts user input to python list.

    Parameters
    ----------
    input (str): User input typed in CLI

    Returns
    -------
    list: Returning list
    """

    if is_list(input):
        return ast.literal_eval(input)
    else:
        return [input]


# Reads contents with UTF-8 encoding and returns str.


def get_controlled_vocabulary(name):

    controlled_vocabularies = {
        "subject": {
            "values": [
                "Agricultural Sciences",
                "Arts and Humanities",
                "Astronomy and Astrophysics",
                "Business and Management",
                "Chemistry",
                "Computer and Information Science",
                "Earth and Environmental Sciences",
                "Engineering",
                "Law",
                "Mathematical Sciences",
                "Medicine, Health and Life Sciences",
                "Physics",
                "Social Sciences",
                "Other",
                "Demo Only",
            ],
            "description": "Controlled list of subjects for DEMO Dataverse",
        },
        "accessRights": {
            "values": ["open", "restricted", "embargoed", "closed"],
            "description": "Controlled list of access rights for RDR",
        },
        "legitimateOptout": {
            "values": [
                "privacy",
                "intellectual property rights",
                "ethical aspects",
                "aspects of dual use",
                "other",
            ],
            "description": "Controlled list of legitimate opt out for RDR",
        },
    }

    return controlled_vocabularies[name]["values"]


def create_tmp_folder():
    directory_name = "tmp"
    root_path = Path(__file__).parent
    new_directory_path = root_path / directory_name

    try:
        new_directory_path.mkdir(exist_ok=True)
    except Exception as e:
        print(f"An error occurred: {e}")

    return new_directory_path.resolve()


def check_typeClass(field):
    match field["typeClass"]:
        case "primitive":
            primitive_field(field)
        case "compound":
            compound_field(field)
        case "controlledVocabulary":
            controlled_vocabulary(field)


def primitive_field(field):
    if re.match(r".*email.*", field["typeName"], re.IGNORECASE):
        field["value"] = get_email(field)
    elif re.match(r".*date.*", field["typeName"], re.IGNORECASE):
        field["value"] = get_date(field)
    else:
        field["value"] = Prompt.ask(
            field["typeName"], default=f"placeholder {field['typeName']}"
        )


def controlled_vocabulary(field):
    controlled_vocabulary_list = get_controlled_vocabulary(field["typeName"])
    value = Prompt.ask(
        f"Choose one {field['typeName']} from the controlled vocabulary (additional values can be added later):",
        choices=controlled_vocabulary_list,
        default=controlled_vocabulary_list[-1],
    )
    if field["multiple"]:
        field["value"] = [value]
    else:
        field["value"] = value


def compound_field(field):
    if field["multiple"]:
        for i in range(len(field["value"])):
            for child_value in field["value"][i].values():
                # print(child_value)
                check_typeClass(child_value)  # check child fields recursively
    else:
        for child_value in field["value"]:
            check_typeClass(
                field["value"][child_value]
            )  # check child fields recursively


def get_email(field):
    email = None
    while not re.match(r"[^@]+@[^@]+\.[^@]+", str(email)):
        email = Prompt.ask(
            f"enter a valid {field['typeName']}", default="placeholder@placeholder.com"
        )
    return email


def get_date(field):
    date = None
    while not re.match(r"\d\d\d\d-\d\d-\d\d", str(date)):
        date = Prompt.ask(
            f"enter a valid {field['typeName']} (YYYY-MM-DD)",
            default=datetime.today().strftime("%Y-%m-%d"),
        )
    return date


def fill_in_md_template(path_to_template):

    with open(path_to_template, "r") as f:
        dataset = json.load(f)

    blocks = dataset["datasetVersion"]["metadataBlocks"]
    block_list = [k for k in blocks]

    for block in block_list:
        for key, value in blocks[block].items():
            if key == "fields":
                for field in value:
                    check_typeClass(field)
        file_path = create_tmp_folder()
        with open(file_path / "tmp_file.json", "w") as f:
            json.dump(dataset, f)
        return str(file_path / "tmp_file.json")
