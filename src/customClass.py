from pyDataverse.models import Dataset


class DemoDataset(Dataset):
    def __init__(self, data=None):
        super().__init__(data=None)
        self.name = "DemoDataset"
        self.baseURL = "https://demo.dataverse.org"
        self.metadataTemplate = "doc/metadata/template_Demo.json"


class RDRDataset(Dataset):

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
        self.name = "RDRDataset"
        self.baseURL = "https://rdr.kuleuven.be/"
        self.metadataTemplate = "doc/metadata/template_RDR.json"


class RDRTestDataset(RDRDataset):
    def __init__(self, data=None):
        #  super extends the original constructor otherwise replacing
        super().__init__(data=None)
        self.name = "RDRTestDataset"
        self.baseURL = "https://www.rdm.libis.kuleuven.be/"
