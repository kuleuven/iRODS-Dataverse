import json
from pyDataverse.api import NativeApi


class Metadatablocks(object):
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
        self.basic_blocks = [  # these are the blocks that you want to include for now we only use citation
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
            # case "havard":
            #     self.dv_url = "https://dataverse.harvard.edu/"
            # case "dans":
            #     self.dv_url = "https://dataverse.nl/"
            # case "DataVerseNL":
            #     self.dv_url = "https://demo.dataverse.nl/dataverse/root"
            case _:
                exit(
                    "this dataverse is not configured: the following installations are available: Demo, RDR, RDR-pilot"
                )

    def check_extra_fields(self):
        """
        This functions checks which extra fields should be added to the metadata document specified by the users
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
        This method takes the typeName of a field and returns a list of the possible
        values for the controlled vocabulary
        """
        if not self.controlled_vocabularies:
            self.get_controlled_vocabularies()

        if name in self.controlled_vocabularies:
            controlled_vocabulary = self.controlled_vocabularies[name]
        return controlled_vocabulary


if __name__ == "__main__":
    dv_installation = input("please provide your installation (RDR, RDR-Pilot, Demo): ")
    api_key = input("please provide your api key: ")
    blocks = Metadatablocks(
        dv_installation,
        api_key,
        [
            "authorAffiliation",
            "datasetContactName",
            "access",
            "accessRights",
            "dateAvailable",
            "legitimateOptout",
            "legalCaseNumber",
        ],
    )
    blocks.create_json_to_upload()
    # blocks.get_controlled_vocabularies()
    #  blocks.write_clean_mdblocks()
