import json
from pyDataverse.api import NativeApi
from pyDataverse.models import Dataset
import requests  # http://docs.python-requests.org/en/master/


class MetadataBlocks(object):
    """
    class to request metadatablocks from dv installation, clean response, create uploadable template, prompt users for
    input & validate using jsonschema
    """

    def __init__(self, dv_installation, dv_api_key, extra_fields=None):
        self.dv_installation = dv_installation
        self.dv_api_key = dv_api_key
        self.dv_url = ""
        self.file_name = f"{self.dv_installation}_md.json"
        self.mdblocks = {}
        self.field_template = {
            "value": "............................",
            "typeClass": "get this from the metadatablocks",
            "multiple": False,
            "typeName": "name of the field",
        }
        self.extra_fields = extra_fields
        self.check_extra_fields()
        self.basic_blocks = [        #these are the blocks that you want to include for now we only use citation   
          #  "geospatial",
          #  "socialscience",
          #  "astrophysics",
          #  "biomedical",
          #  "journal",
            "citation",
          #  "computationalworkflow",
        ]
        self.controlled_vocabularies = {}
        self.schema = ""

    ########## functions to dynamically get & clean metadatablocks ##############
    ####  the API returns a number of blocks and each block contains a number of fields = metadata

    def set_dv_url(self):
        match self.dv_installation.lower():
            case "rdr-pilot":
                self.dv_url = "https://www.rdm.libis.kuleuven.be/"
            case "demo":
                self.dv_url = "https://demo.dataverse.org"
            case "rdr":
                self.dv_url = "https://rdr.kuleuven.be/"
            case "havard":
                self.dv_url = "https://dataverse.harvard.edu/"
            case "dans":
                self.dv_url = "https://dataverse.nl/"
            case "DataVerseNL":
                self.dv_url = "https://demo.dataverse.nl/dataverse/root"
            case _:
                exit(
                    "this dataverse is not configured: the following installations are available: demo, RDR, RDR-Pilot, Harvard, DANS"
                )

    def check_extra_fields(self):
        """This functions checks which extra fields should be added to the metadata document specified by the users
        these are fields that are not listed as required in the template but can be added by the users
        """
        if self.extra_fields == None:
            self.extra_fields = []
        else:
            pass

    def get_mdblocks(self):
        """
        gets metadatablocks from dataverse

        """
        self.set_dv_url()
        print(self.dv_url)
        api = NativeApi(self.dv_url, self.dv_api_key)
        mdblocks_overview = api.get_metadatablocks().json()
        self.mdblocks = {}
        for block in mdblocks_overview["data"]:
            self.mdblock = api.get_metadatablock(block["name"]).json()
            self.mdblocks[block["name"]] = self.mdblock["data"]

    def remove_childfields(self):
        """
        removes the fields from the top level that already exist as childfields of a compound field

        Parameters:
        ----------
        block: block name (string)

        """
        for block in [k for k in self.mdblocks]:
            compound_fields = {
                k: v
                for k, v in self.mdblocks[block]["fields"].items()
                if v["typeClass"] == "compound"
            }  # get all the compound fields
            double_fields = {}
            for key in compound_fields:  # make a list with all the child fields
                double_fields[key] = [k for k in compound_fields[key]["childFields"]]
            for field in double_fields:
                for child_field in double_fields[field]:
                    del self.mdblocks[block]["fields"][
                        child_field
                    ]  # delete the child fields from the top level

    def write_clean_mdblocks(self):
        """
        gets metadatablocks from api, cleans them & write to file

        """
        self.get_mdblocks()
        self.remove_childfields()
        with open(f"{self.dv_installation}_metadatablocks_full.json", "w") as f:
            json.dump(self.mdblocks, f)

    def clean_mdblocks(self):
        """
        gets metadatablocks from api and cleans them
        """
        self.get_mdblocks()
        self.remove_childfields()

    def get_datasetSchema(self):
        headers = {"X-Dataverse-key": self.dv_api_key}
        self.schema = requests.get(
            f"https://rdr.kuleuven.be/api/dataverses/{self.dv_installation.lower()}/datasetSchema",
            headers=headers,
        )

    def write_schema(self):
        with open(f"doc/schemas/{self.dv_installation}_schema.json", "w") as f:
            json.dump(self.schema.json(), f)

    ###### get all the controlled vocabularies ###############

    def get_controlled_vocabularies(self):
        """
        This function gets all the controlled vocabularies
        """
        if not self.mdblocks:  # create md_blocks if empty
            self.clean_mdblocks()
        for k, v in self.mdblocks["citation"]["fields"].items():
            if v["isControlledVocabulary"]:
                self.controlled_vocabularies[k] = v["controlledVocabularyValues"]
            if "childFields" in k:
                for ck, cv in k["childFields"].items():
                    if cv["isControlledVocabulary"]:
                        self.controlled_vocabularies[ck] = cv[
                            "controlledVocabularyValues"
                        ]
        # print(self.controlled_vocabularies)

    ########## create templates ##############

    def create_field(self, value, typeClass, compound=None):
        """
        This function makes a copy of the template (field_info) and fills in the necessary
        information based on the provided parameters: either compound or not compound
        Parameters:
        ---------
        field_info : dictionary
        value: dictionary
        typeClass = string
        compound: optional parameter

        Returns:
        --------
        field

        """
        new_field = self.field_template.copy()
        if compound is not None:
            new_field["value"] = compound
        new_field["typeClass"] = typeClass
        new_field["multiple"] = value["multiple"]
        new_field["typeName"] = value["name"]
        return new_field

    def add_child(self, cv, ck):
        """
        add childfields and return dictionary

        Parameters:
        ---------
        cv: child value
        ck: child key
        extra_fields: list with extra fields that you want to include

        Returns:
        --------
        filled in field template or false

        """
        if cv["isRequired"] or ck in self.extra_fields:
            if cv["typeClass"] == "primitive":
                new_field = self.create_field(cv, "primitive")
                return new_field
            elif cv["typeClass"] == "controlledVocabulary":
                new_field = self.create_field(cv, "controlledVocabulary")
                return new_field
            else:
                return False

    def add_required(self, all_blocks, block):
        """
        function to add required fields, goes through all the blocks (citation, ...) and checks if required
        """
        # field_info_template = get_field_info_template()
        all_fields = []
        for k, v in all_blocks[block]["fields"].items():
            if v["isRequired"] or k in self.extra_fields:  # check if required
                if v["typeClass"] == "primitive":  # for typeClass primitive do this
                    new_field = self.create_field(v, "primitive")
                    all_fields.append(new_field)
                elif v["typeClass"] == "compound":  # for typeClass compound do this
                    my_dict = {}
                    for ck, cv in v["childFields"].items():
                        new_field = self.add_child(cv, ck)
                        if new_field:
                            my_dict[cv["name"]] = new_field
                    if v["multiple"]:
                        new_field = self.create_field(
                            v, "compound", [my_dict]
                        )  # put all the dicts in a list
                    else:
                        new_field = self.create_field(
                            v, "compound", my_dict
                        )  # put all the dicts in a list
                    all_fields.append(new_field)
                elif (
                    v["typeClass"] == "controlledVocabulary"
                ):  # for typeClass controlledVoc do this
                    new_field = self.create_field(v, "controlledVocabulary")
                    all_fields.append(new_field)
        return all_fields

    def create_json_to_upload(self):
        """
        This function creates & writes the json

        """
        self.clean_mdblocks()
        # do multiple blocks go in a list?! --> negative
        block_dict = {}
        for block in self.basic_blocks:
            try:
                all_field_info = self.add_required(self.mdblocks, block)
                if len(all_field_info) != 0:
                    block_template = {
                        "fields": all_field_info,
                        "displayName": self.mdblocks[block]["displayName"],
                    }
                    block_dict[block] = block_template
            except KeyError:  # possible that not all basic keys are in dv installation
                pass

        total_template = {"datasetVersion": {"metadataBlocks": block_dict}}
        with open(f"{self.dv_installation}_md.json", "w") as f:
            json.dump(total_template, f)

    def find_controlled_vocabulary(self, name):
        """
        Checks for controlled vocabularies
        """
        if not self.controlled_vocabularies:
            self.get_controlled_vocabularies()

        if name in self.controlled_vocabularies:
            controlled_vocabulary = self.controlled_vocabularies[name]
        return controlled_vocabulary

    def fill_in_md_template(self, file_name=None):
        """
        prompts user to fill in values for md upload form

        Optional param: file_name
        """

        if file_name == None:
            file_name = self.file_name

        with open(file_name, "r") as f:
            dataset = json.load(f)

        blocks = dataset["datasetVersion"]["metadataBlocks"]
        block_list = [k for k in blocks]

        for block in block_list:
            for key, value in blocks[block].items():
                if key == "fields":
                    for field in value:
                        if isinstance(field["value"], list):
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
                                    + str(self.find_controlled_vocabulary(name))
                                )
                                string = input(f"{name}: ")
                                field["value"] = string.split(",")
                            else:
                                field["value"] = input(f"{name}: ")

            with open(file_name, "w") as f:
                json.dump(dataset, f)

    def show_controlled_vocabularies(self, name):
        match name:
            case "subject":
                voc = (
                    [
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
                )
            case "departmentFaculty":
                voc = (
                    [
                        "Associated Faculty of Arts",
                        "Faculty of Arts",
                        "Department of Architecture",
                        "Faculty of Architecture",
                        "Department of Biology",
                        "Faculty of Bioscience Engineering",
                        "Department of Biosystems (BIOSYST)",
                        "Faculty of Canon Law",
                        "Department of Cardiovascular Sciences",
                        "Department of Cellular and Molecular Medicine",
                        "Department of Chemical Engineering (CIT)",
                        "Department of Chemistry",
                        "Department of Chronic Diseases and Metabolism",
                        "Department of Civil Engineering",
                        "Department of Computer Science",
                        "Department of Development and Regeneration",
                        "DOC - Research Coordination Office",
                        "Department of Earth and Environmental Sciences",
                        "Faculty of Economics and Business (FEB)",
                        "Department of Electrical Engineering (ESAT)",
                        "Faculty of Engineering Science",
                        "Faculty of Engineering Technology",
                        "European Centre for Ethics",
                        "HIVA",
                        "Department of Human Genetics",
                        "ILT",
                        "Department of Imaging and Pathology",
                        "Interfaculty Centre for Agrarian History",
                        "KADOC",
                        "KU Leuven Libraries",
                        "Faculty of Law",
                        "Lstat",
                        "LUCAS",
                        "Department of Materials Engineering",
                        "Department of Mathematics",
                        "Department of Mechanical Engineering",
                        "Faculty of Medicine",
                        "Department of Microbial and Molecular Systems (M\u00b2S)",
                        "Department of Microbiology, Immunology and Transplantation",
                        "Faculty of Movement and Rehabilitation Sciences",
                        "Department of Movement Sciences",
                        "Department of Neurosciences",
                        "Department of Oncology",
                        "Department of Oral Health Sciences",
                        "Faculty of Pharmaceutical Sciences",
                        "Department of Pharmaceutical and Pharmacological Sciences",
                        "Institute of Philosophy",
                        "Department of Physics and Astronomy",
                        "Faculty of Psychology and Educational Sciences",
                        "Department of Public Health and Primary Care",
                        "Department of Rehabilitation Sciences",
                        "Faculty of Science",
                        "Faculty of Social Sciences",
                        "Faculty of Theology and Religious Studies",
                        "University Administration and Central Services",
                        "Other",
                    ],
                )
        return voc


if __name__ == "__main__":
    dv_installation = input("please provide your installation (RDR, RDR-Pilot, Demo): ")
    api_key = input("please provide your api key: ")
    blocks = MetadataBlocks(
        dv_installation,
        api_key,
        ["authorAffiliation", "datasetContactName"],
    )
    blocks.create_json_to_upload()
    blocks.fill_in_md_template()
    # blocks.get_controlled_vocabularies()
  
