"""Reads CLI input with UTF-8 encoding and returns filled-in metadata template"""

import json
import ast
from rich.prompt import Prompt
from pathlib import Path
import re
from datetime import datetime


def to_list(input: str) -> list:
    """Converts user input to python list given a specific input pattern"""

    input_as_list = ast.literal_eval(input)
    if isinstance(input_as_list, list):  # TO DO: change with click
        return input_as_list
    else:
        return [input]


def get_controlled_vocabulary_list(name):
    """Hard-coded dictionary with necessary controlled vocabularies."""

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

    return controlled_vocabularies[name][
        "values"
    ]  # TODO move to class definition and make a method


def check_type_class(field):
    """Checks typeClass (primive, compound, controlled vocabulary) for each field and redirects to appropriate method."""

    match field["typeClass"]:
        case "primitive":
            get_primitive_field(field)
        case "compound":
            compound_field(field)
        case "controlledVocabulary":
            get_controlled_vocabulary(field)  # TO DO: Check when we use click


def get_primitive_field(field):
    """Modify field value for a primitive field based on interactive user input"""

    if re.match(r".*email.*", field["typeName"], re.IGNORECASE):
        field["value"] = get_email(field)
    elif re.match(r".*date.*", field["typeName"], re.IGNORECASE):
        field["value"] = get_date(field)
    else:
        field["value"] = Prompt.ask(
            field["typeName"], default=f"placeholder {field['typeName']}"
        )


def get_controlled_vocabulary(field):
    """Gets value for a controlled vocabulary from user"""

    controlled_vocabulary_list = get_controlled_vocabulary_list(field["typeName"])
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
    """Iterate through a compound field and check child fields recursively"""

    if field["multiple"]:
        for instance in field["value"]:
            for child_value in instance.values():
                check_type_class(child_value)
    else:
        for child_value in field["value"].values():
            check_type_class([child_value])


def get_email(field):
    """Get email in correct format string@string.string"""

    email = None
    while not re.match(r"[^@]+@[^@]+\.[^@]+", str(email)):
        email = Prompt.ask(
            f"enter a valid {field['typeName']}", default="placeholder@placeholder.com"
        )
    return email


def get_date(field):
    """Get date in correct format YYYY-MM-DD"""

    date = None
    while not re.match(r"\d\d\d\d-\d\d-\d\d", str(date)):
        date = Prompt.ask(
            f"enter a valid {field['typeName']} (YYYY-MM-DD)",
            default=datetime.today().strftime("%Y-%m-%d"),
        )
    return date


def fill_in_md_template(path_to_template):
    """Allow user to fill in the template and return as dictionary"""

    with open(path_to_template, "r") as f:
        dataset = json.load(f)

    blocks = dataset["datasetVersion"][
        "metadataBlocks"
    ]  # get the blocks from the dataset

    for block in blocks:
        for key, value in blocks[block].items():
            if key == "fields":
                for field in value:
                    check_type_class(field)
    return dataset
