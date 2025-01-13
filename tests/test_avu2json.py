import unittest
from importlib.resources import files
from irods2dataverse.avu2json import (
    parse_json_metadata,
    update_template,
    extract_template,
    fill_in_template,
)


class TestFieldTransformation(unittest.TestCase):
    def setUp(self):
        self.metadatadict = {
            "author": {
                "authorAffiliation": "KU Leuven",
                "authorName": "Doe, Jane",
            },
            "datasetContact": {
                "datasetContactEmail": "user.name@kuleuven.be",
                "datasetContactName": "Doe, Jane",
            },
            "dsDescription": [
                {
                    "dsDescriptionValue": "This is a minimal end-to-end implementation for iRODS-Dataverse integration, a KU Leuven and SURF collaboration"
                }
            ],
            "subject": ["Demo Only"],
            "title": "Minimum Viable Workflow - 16 May 2024",
        }
        self.schema_demo_path = files("resources").joinpath(
            "mango2dv-demo-1.0.0-published.json"
        )

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

        for property in ["typeClass", "multiple", "typeName"]:
            with self.subTest(property=property):
                self.assertEqual(title_template[property], new_title[property])
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
        for property in ["typeClass", "multiple", "typeName"]:
            with self.subTest(property=property):
                self.assertEqual(author_template[property], new_author[property])

        original_authorname = author_template["value"][0]["authorName"]
        new_authorname = new_author["value"][0]["authorName"]
        for property in ["typeClass", "multiple", "typeName"]:
            with self.subTest(property=property):
                self.assertEqual(
                    original_authorname[property], new_authorname[property]
                )
        self.assertEqual(
            self.metadatadict["author"]["authorName"], new_authorname["value"]
        )

    def test_rewriting_template(self):
        template_path = files("resources").joinpath("template_Demo.json")
        demo_template = extract_template(template_path)
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
