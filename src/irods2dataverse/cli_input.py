from .metadatablocks import Metadatablocks
import json
import importlib.resources 

# Reads contents with UTF-8 encoding and returns str.

def get_controlled_vocabulary(dv_installation, api_key, field):

    blocks = Metadatablocks(dv_installation, api_key)
    controlled_vocabulary = blocks.find_controlled_vocabulary(field)
    return controlled_vocabulary


def get_filename(dv_installation):
    match dv_installation:
        case "RDR":
            return "template_RDR.json"
        case "Demo":
            return "template_Demo.json"
        case "RDR-pilot":
            return "template_RDR-pilot.json"
        


def fill_in_md_template(dv_installation, api_key):
    """
    prompts user to fill in values for md upload form

    """
    with importlib.resources.path('resources', get_filename(dv_installation)) as resource_path:
        filename = resource_path

    with open(filename , "r") as f:
        dataset = json.load(f)

    blocks = dataset["datasetVersion"]["metadataBlocks"]
    block_list = [k for k in blocks]

    for block in block_list:
        for key, value in blocks[block].items():
            if key == "fields":
                for field in value:
                    if isinstance(field["value"], list) and field["typeClass"] != "controlledVocabulary":
                        for i in range(len(field["value"])):
                            for child_value in field["value"][i].values():
                                name = child_value["typeName"]
                                child_value["value"] = input(f"{name}: ")
                    else:
                        name = field["typeName"]
                        if field["typeClass"] == "controlledVocabulary":
                            print(
                                """controlled vocabulary: (separate with , (no spaces) )
                                    """
                                + str(get_controlled_vocabulary(dv_installation, api_key, name))
                            )
                            string = input(f"{name}: ")
                            field["value"] = string.split(",")
                        else:
                            field["value"] = input(f"{name}: ")
        with open(filename, "w") as f:
            json.dump(dataset, f)
        
    return filename


