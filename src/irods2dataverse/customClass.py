from pyDataverse.models import Dataset
from importlib.resources import files


class CustomDataset(Dataset):

    @property
    def metadata_template(self):
        return files("resources").joinpath(self._metadataTemplate)

    @property
    def mango_schema(self):
        return files("resources").joinpath(self._mangoSchema)


class DemoDataset(CustomDataset):
    def __init__(self, data=None):
        super().__init__(data=None)
        self.alias = "demo"
        self.name = "DemoDataset"
        self.baseURL = "https://demo.dataverse.org"
        self._metadataTemplate = "template_Demo.json"
        self._mangoSchema = "mango2dv-demo-1.0.0-published.json"


class RDRDataset(CustomDataset):

    def __init__(self, data=None):
        #  super extends the original constructor otherwise replacing
        super().__init__(data=None)
        # self. ==> instance attribute instead of class attribute
        self._Dataset__attr_import_dv_up_citation_fields_values.append(
            "technicalFormat"
        )
        self._Dataset__attr_import_dv_up_citation_fields_values.append("access")
        self._Dataset__attr_dict_dv_up_required = (
            self._Dataset__attr_dict_dv_up_required
            + ["access", "keyword", "technicalFormat"]
        )
        self._Dataset__attr_dict_dv_up_required.remove("subject")
        self._Dataset__attr_dict_dv_up_type_class_primitive.append("technicalFormat")
        self._Dataset__attr_dict_dv_up_type_class_compound.append("access")
        self._Dataset__attr_dict_dv_up_type_class_controlled_vocabulary = (
            self._Dataset__attr_dict_dv_up_type_class_controlled_vocabulary
            + ["accessRights", "legitimateOptout"]
        )
        self.alias = "rdr"
        self.name = "RDRDataset"
        self.baseURL = "https://rdr.kuleuven.be/"
        self._metadataTemplate = "template_RDR.json"
        self._mangoSchema = "mango2dv-rdr-1.0.0-published.json"


class RDRPilotDataset(RDRDataset):
    def __init__(self, data=None):
        super().__init__(data=None)
        self.alias = "rdr"
        self.name = "RDRPilotDataset"
        self.baseURL = "https://www.rdm.libis.kuleuven.be/"
        self._metadataTemplate = "template_RDR-pilot.json"
        self._mangoSchema = "mango2dv-rdr-1.0.0-published.json"
