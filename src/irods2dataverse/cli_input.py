from .metadatablocks import Metadatablocks
import json
import importlib.resources 
from rich.prompt import Prompt, Confirm


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
                        "Demo Only"
                    ],
                    "description": "Controlled list of subjects for DEMO Dataverse"
                }
            }
    
    return controlled_vocabularies[name]["values"]
    

    

def get_filename(dv_installation):
    match dv_installation:
        case "RDR":
            return "template_RDR.json"
        case "Demo":
            return "template_Demo.json"
        case "RDR-pilot":
            return "template_RDR-pilot.json"
        


def fill_in_md_template(path_to_template):
    """
    prompts user to fill in values for md upload form

    """

    with open(path_to_template , "r") as f:
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
                                child_value["value"] = Prompt.ask(name, default=f"placeholder {name}")
                    else:
                        name = field["typeName"]
                        if field["typeClass"] == "controlledVocabulary":
                            controlled_vocabulary_list = get_controlled_vocabulary(name)
                            string = Prompt.ask(f"Choose a {name} from the controlled vocabulary:", choices=controlled_vocabulary_list, default=controlled_vocabulary_list[0])
                            field["value"] = string
                        else:
                            field["value"] = Prompt.ask(name, default=f"placeholder {name}")
        print(blocks)
        with open("TEMPFILE_changeme.json", "w") as f:
            json.dump(dataset, f)
        
    #return TEMPFILE_changeme


