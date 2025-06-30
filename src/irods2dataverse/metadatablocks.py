import json
from pyDataverse.api import NativeApi


class Metadatablocks(object):
    """Class to request metadatablocks from dv installation and create template.
    """

    def __init__(self, dv_installation, dv_api_key, extra_fields=[]):
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
        self.basic_blocks = [  # these are the blocks that you want to include for now we only use citation
            #  "geospatial",
            #  "socialscience",
            #  "astrophysics",
            #  "biomedical",
            #  "journal",
            "citation",
            #  "computationalworkflow",
        ]
        self.all_controlled_vocabularies = {}
        self.schema = ""

    def _set_dv_url(self):
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


    def _set_mdblocks(self):
        """Sets instance variable mdblocks."""
        self._set_dv_url()
        api = NativeApi(self.dv_url, self.dv_api_key)
        mdblocks_overview = api.get_metadatablocks().json()
        self.mdblocks = {}
        for block in mdblocks_overview["data"]:
            self.mdblock = api.get_metadatablock(block["name"]).json()
            self.mdblocks[block["name"]] = self.mdblock["data"]

    def _remove_childfields(self):
        """Removes the fields from the top level that already exists as childfields of a compound field"""
        for block in self.mdblocks:
            compound_fields = {
                k: v
                for k, v in self.mdblocks[block]["fields"].items()
                if v["typeClass"] == "compound"
            }  # get all the compound fields
            double_fields = {}
            for key in compound_fields:  # make a list with all the child fields
                double_fields[key] = list(compound_fields[key]["childFields"])
            for field in double_fields:
                for child_field in double_fields[field]:
                    del self.mdblocks[block]["fields"][
                        child_field
                    ]  # delete the child fields from the top level

    def write_clean_mdblocks(self):
        """Gets metadatablocks from api, cleans them & writes to a json document."""
        self._set_mdblocks()
        self._remove_childfields()
        with open(f"{self.dv_installation}_metadatablocks_full.json", "w") as f:
            json.dump(self.mdblocks, f)

    def _clean_mdblocks(self):
        """Gets metadatablocks from api and cleans them."""
        self._set_mdblocks()
        self._remove_childfields()


    def set_all_controlled_vocabularies(self):
        """ This function gets all the controlled vocabularies
        """
        if not self.mdblocks:  # create md_blocks if empty
            self._clean_mdblocks()
        for k, v in self.mdblocks["citation"]["fields"].items():
            if v["isControlledVocabulary"]:
                self.all_controlled_vocabularies[k] = v["controlledVocabularyValues"]
            if "childFields" in k:
                for ck, cv in k["childFields"].items():
                    if cv["isControlledVocabulary"]:
                        self.all_controlled_vocabularies[ck] = cv[
                            "controlledVocabularyValues"
                        ]
        # print(self.all_controlled_vocabularies)


    def create_field(self, value: dict, typeClass: str, compound=None) -> dict:
        """ This function makes a copy of the template (field_info) and fills in
        the necessary information based on the provided parameters: either 
        compound or not compound.
        """
        new_field = self.field_template.copy()
        if compound is not None:
            new_field["value"] = compound
        new_field["typeClass"] = typeClass
        new_field["multiple"] = value["multiple"]
        new_field["typeName"] = value["name"]
        return new_field

    def add_child(self, child_value: dict, child_key: str):
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
        if child_value["isRequired"] or child_key in self.extra_fields:
            if child_value["typeClass"] == "primitive":
                new_field = self.create_field(child_value, "primitive")
                return new_field
            elif child_value["typeClass"] == "controlledVocabulary":
                new_field = self.create_field(child_value, "controlledVocabulary")
                return new_field
            else:
                return False

    def add_required(self, all_blocks: dict, block: str):
        """Function to add required fields, goes through all the blocks (citation, ...) and checks if required
        """
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
        """This function creates & writes the json"""
        self._clean_mdblocks()
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

    def find_controlled_vocabulary(self, name: str) -> dict:
        """ This method takes the typeName of a field and
        returns a list of the possible values for the controlled vocabulary
        """
        if not self.all_controlled_vocabularies:
            self.get_all_controlled_vocabularies()

        if name in self.all_controlled_vocabularies:
            controlled_vocabulary = self.all_controlled_vocabularies[name]
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
    # blocks.get_all_controlled_vocabularies()
    #  blocks.write_clean_mdblocks()
