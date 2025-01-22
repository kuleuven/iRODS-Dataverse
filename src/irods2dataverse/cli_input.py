from .metadatablocks import Metadatablocks
import json
from rich.prompt import Prompt, Confirm
from pathlib import Path


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
    

def create_tmp_folder():
    directory_name = "tmp"
    root_path = Path(__file__).parent
    new_directory_path = root_path / directory_name

    try:
        new_directory_path.mkdir(exist_ok=True)
    except Exception as e:
        print(f"An error occured: {e}")
    
    return new_directory_path.resolve()



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
                                if name == "datasetContactEmail":
                                    child_value["value"] = Prompt.ask(name, default="placeholder@placeholder.com")
                                else:
                                    child_value["value"] = Prompt.ask(name, default=f"placeholder {name}")
                    else:
                        name = field["typeName"]
                        if field["typeClass"] == "controlledVocabulary":
                            controlled_vocabulary_list = get_controlled_vocabulary(name)
                            string = Prompt.ask(f"Choose one {name} from the controlled vocabulary (additional values can be added later):", choices=controlled_vocabulary_list, default="Other")
                            field["value"] = [string]
                        else:
                            field["value"] = Prompt.ask(name, default=f"placeholder {name}")
        file_path = create_tmp_folder()
        with open(file_path / "tmp_file.json", "w") as f:
            json.dump(dataset, f)
        return str(file_path / "tmp_file.json")



        
    #return TEMPFILE_changeme


