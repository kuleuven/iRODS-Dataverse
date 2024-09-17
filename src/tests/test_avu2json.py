import unittest
from avu2json import *


class TestFieldTransformation(unittest.TestCase):
    def setUp(self):
        self.metadatadict = {
            "author": {
                "authorAffiliation": "KU Leuven",
                "authorName": "Kafetzaki, Danai",
            },
            "datasetContact": {
                "datasetContactEmail": "danai.kafetzaki@kuleuven.be",
                "datasetContactName": "Kafetzaki, Danai",
            },
            "dsDescription": [
                {
                    "dsDescriptionValue": "This is a minimal end-to-end implementation for iRODS-Dataverse integration, a KU Leuven and SURF collaboration"
                }
            ],
            "subject": ["Demo Only"],
            "title": "Minimum Viable Workflow - 16 May 2024",
        }
        self.schema_demo_path = "../doc/metadata/mango2dv-demo-1.0.0-published.json"

    def test_validation(self):
        validated_metadata = parse_json_metadata(
            self.schema_demo_path, self.metadatadict
        )
        self.assertDictEqual(self.metadatadict, validated_metadata)

    def test_fill_in_simple_field(self):
        title_template = {
            "value": "...Title...",
            "typeClass": "primitive",
            "multiple": False,
            "typeName": "title",
        }
        new_title = update_template(title_template, self.metadatadict)
        self.assertEqual(title_template["typeClass"], new_title["typeClass"])
        self.assertEqual(title_template["multiple"], new_title["multiple"])
        self.assertEqual(title_template["typeName"], new_title["typeName"])
        self.assertEqual(self.metadatadict["title"], new_title["value"])

    def test_fill_in_composite_field(self):
        author_template = {
            "value": [
                {
                    "authorName": {
                        "value": "...LastName..., ...FirstName...",
                        "typeClass": "primitive",
                        "multiple": False,
                        "typeName": "authorName",
                    },
                    "authorAffiliation": {
                        "value": "...Affiliation...",
                        "typeClass": "primitive",
                        "multiple": False,
                        "typeName": "authorAffiliation",
                    },
                }
            ],
            "typeClass": "compound",
            "multiple": False,
            "typeName": "author",
        }
        new_author = update_template(author_template, self.metadatadict)
        self.assertEqual(author_template["typeClass"], new_author["typeClass"])
        self.assertEqual(author_template["multiple"], new_author["multiple"])
        self.assertEqual(author_template["typeName"], new_author["typeName"])

        original_authorname = author_template["value"][0]["authorName"]
        new_authorname = new_author["value"][0]["authorName"]
        self.assertEqual(original_authorname["typeClass"], new_authorname["typeClass"])
        self.assertEqual(original_authorname["multiple"], new_authorname["multiple"])
        self.assertEqual(original_authorname["typeName"], new_authorname["typeName"])
        self.assertEqual(
            self.metadatadict["author"]["authorName"], new_authorname["value"]
        )

    def test_rewriting_template(self):
        demo_template = extract_template("../doc/metadata/template_Demo.json")
        self.assertIsInstance(demo_template, dict)

        fields = demo_template["datasetVersion"]["metadataBlocks"]["citation"]["fields"]
        original_n_fields = len(fields)
        original_keys = [x["typeName"] for x in fields]
        original_values = [x["value"] for x in fields]
        fill_in_template(demo_template, self.metadatadict)
        self.assertEqual(len(fields), original_n_fields)
        self.assertEqual([x["typeName"] for x in fields], original_keys)
        self.assertNotEqual([x["value"] for x in fields], original_values)


if __name__ == "__main__":
    unittest.main()
